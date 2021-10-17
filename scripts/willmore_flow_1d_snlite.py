"""
in steps s d=1000 n=2
in verts_in v
in time_step s d=0.01 n=2
in frame_num s d=0 n=2
out verts_out v
"""

def setup():
    
    import numpy as np
    
    class CurvatureFlow1d():

        verts_list = [[]]
        step_num = 0
        dt = 0.01
        normal_2d = np.array([0.0, 0.0, 1.0])
        generated_verts = []
        
        def __init__(self, step_num, verts_list, dt):
        
            self.step_num = step_num
            self.dt = dt
            self.verts_list = verts_list

        # Process curvature flow for each vertices list
        def process(self):
            
            for node_datas in self.verts_list:
                nodes = np.array(node_datas)
                lengths = self.computeLengths(nodes)
            
                gen_verts_dic = {}
                
                # Set initial status
                gen_verts_dic[0] = nodes.tolist()
        
                percent_prev = 0
                for step in range(1, self.step_num):
                    
                    nodes = self.curvature_flow(nodes, lengths)
                    
                    # Store results for each step                    
                    gen_verts_dic[step] =  nodes.tolist()

                    percent = 100 * (step + 1) // self.step_num # percent completed
                    if percent != percent_prev:
                        percent_prev = percent
                        print(str(percent).zfill(2), "%")

                # Store generated verts and edges                
                self.generated_verts.append(gen_verts_dic)
            
        # Compute edge lengths
        def computeLengths(self, nodes):
            nodes_lshift = np.roll(nodes, -1, axis=0)
            vectors = nodes_lshift - nodes
            lengths = np.linalg.norm(vectors, axis=1)
            return lengths

        # Compute an angle between two vectors (range: -pi < angle < pi)
        def computeAngle(self, vec1, vec2):
            dot = vec1.dot(vec2)
            mat_v = np.stack((vec1, vec2, self.normal_2d), axis=1)
            det = np.linalg.det(mat_v)
            angle = np.arctan2(det, dot)
            return angle
            
        # Compute angles between each pair of vectors from two vector lists (range: -pi < angle < pi)
        def computeAngles(self, vecs1, vecs2):
            normals = np.full((vecs1.shape[0], 3), self.normal_2d)
            mat_v = np.stack((vecs1, vecs2, normals), axis=1)
            dot = np.einsum('ij,ij->i', vecs1, vecs2)
            det = np.linalg.det(mat_v)
            angles = np.arctan2(det, dot)
            return angles
            
        # Compute curvatures around each vertex
        def get_curvatures(self, nodes):
            curvatures = np.zeros(len(nodes))
            
            nodes_lshift = np.roll(nodes, -1, axis=0)
            nodes_rshift = np.roll(nodes, 1, axis=0)            
            e1 = nodes - nodes_rshift
            e2 = nodes_lshift - nodes
            l1 = np.linalg.norm(e1, axis=1)
            l2 = np.linalg.norm(e2, axis=1)

            angles = self.computeAngles(e1, e2)
            kappa = 2 * angles / (l1+l2)
            
            curvature = kappa
            return curvature
        
        # Build constraints of the flow direction
        def buildConstraints(self, nodes, f):
            x1 = np.ones(f.shape[0])
            x2 = nodes[:,0]
            x3 = nodes[:,1]
            A = np.stack((x1, x2, x3), axis=1)
            q, r = np.linalg.qr(A)
            
            f_ = f - np.sum(np.dot(f.T, q) * q, axis=1)
            
            return f_
        
        # Recover curvature tangents and positions
        def updateCurve(self, nodes, lengths, curvature):
            
            nodes_lshift = np.roll(nodes, -1, axis=0)
            nodes_rshift = np.roll(nodes, 1, axis=0)            
            e1 = nodes - nodes_rshift
            e2 = nodes_lshift - nodes
            l1 = np.linalg.norm(e1, axis=1)
            l2 = np.linalg.norm(e2, axis=1)
            
            baseline = np.array([1,0,0])
            angle0 = self.computeAngle(baseline, (nodes[1]-nodes[0]))
            
            delta = ((l1+l2)/2) * curvature
            angle = np.cumsum(delta)
            angle = angle - (angle[0] - angle0)
            new_nodes = np.zeros_like(nodes)
            new_nodes[0] = nodes[0]
            for i in range(1, len(nodes)):
                T = np.array([lengths[i-1]*np.cos(angle[i-1]), lengths[i-1]*np.sin(angle[i-1]), 0.0])
                new_nodes[i] = new_nodes[i-1] + T
            # for i in range(1, len(nodes) + 1):
                # T = np.array([lengths[(i-1) % len(nodes)]*np.cos(angle[(i-1) % len(nodes)]), lengths[(i-1) % len(nodes)]*np.sin(angle[(i-1) % len(nodes)]), 0.0])
                # new_nodes[i % len(nodes)] = new_nodes[(i-1) % len(nodes)] + T

            return new_nodes
            
        # Curvature flow procedure
        def curvature_flow(self, nodes, lengths):
            
            kappas = self.get_curvatures(nodes)
            velocities = self.buildConstraints(nodes, -kappas)
            new_kappas = kappas + self.dt * velocities
            nodes = self.updateCurve(nodes, lengths, new_kappas)
            
            return nodes
                     
    if verts_in is None:
        raise Exception("No data.")

    cf = CurvatureFlow1d(steps, verts_in, time_step)
    cf.process()
    
verts_out = [gv.get(frame_num) for gv in cf.generated_verts]

