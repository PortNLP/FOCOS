import pandas as pd
import numpy as np

def get_connections(practice):
    """
    Get the connections/edges for a specific practice
    :param practice: String
    :return: Dict {practice_name : value}
    """

    file_name = "model/FCM-HROT_InterventionsIncluded.csv" # directory is relative to app.py
    df = pd.read_csv(file_name,index_col=0)

    connections = df.loc[practice]
    connections = connections.to_dict() # Dict {String : Float}
    connections = {k:v for (k,v) in connections.items() if v != 0} # Filter out zero values

    return connections

def run_inference(interventions, principles, modified_connections={}):
    """
    Run FCM inference for a set of interventions (changes in practices)
    :param interventions: Dict {intervention_name : value}
    :param principles: List of Strings
    :param modified_connections: Dict {practice : connections}
    :return: List of Floats
    """

    file_name = "model/FCM-HROT_InterventionsIncluded.csv" # directory is relative to app.py
    df = pd.read_csv(file_name,index_col=0)

    # change connections if the model is being critiqued
    if modified_connections:
        connections = modified_connections["connections"]
        if connections:
            for key, val in connections.items():
                #print(df.loc[modified_connections["practice"], key])
                df.loc[modified_connections["practice"], key] = float(val)

    n_concepts = df.shape[0]

    Adj_matrix = np.zeros((n_concepts,n_concepts))
    activation_vec = np.ones(n_concepts)

    # remove the edges with a weight less than a specific number (e.g. 0.1) 
    noise_threshold = 0 # use full FCM without removing noises 
    if noise_threshold == 0:
        Adj_matrix = df.to_numpy()
    else:
        for i in range (n_concepts):
            for j in range (n_concepts):
                if abs(df.iat[i,j])<=noise_threshold:
                    Adj_matrix[i,j]=0
                else:
                    Adj_matrix[i,j]=df.iat[i,j]

    function_type = "tanh" # Hyperbolic tangent 
    infer_rule = "k" # Kosko

    intervention_indexes = []
    vals = []
    for key, val in interventions.items():
        intervention_indexes.append(df.columns.get_loc(key))
        vals.append(val)

    steady_state = np.zeros(n_concepts) # steady_state is 0 for this model
    #steady_state = infer_steady(init_vec = activation_vec, AdjmT = Adj_matrix.T, 
    #                            n = n_concepts, f_type = function_type , infer_rule = infer_rule)
    scenario_state = infer_scenario(intervention_indexes = intervention_indexes, vals = vals, init_vec = activation_vec, AdjmT = Adj_matrix.T, 
                                n = n_concepts, f_type = function_type, infer_rule = infer_rule)
    changes = scenario_state - steady_state

    principle_indexes = []
    for name in principles:
        pi = df.columns.get_loc(name)
        principle_indexes.append(pi)


    effects = changes[principle_indexes] * 100 # Convert to percent
    effects = list(effects.astype(float)) # Convert to list of 64 bit floats so it's serializable
    return effects

def infer_steady(init_vec, AdjmT, n, f_type="tanh", infer_rule="k", epsilon=0.00001):
    act_vec_old= init_vec
    
    resid = 1
    while resid > epsilon:
        act_vec_new = np.zeros(n)
        x = np.zeros(n)
        
        # Inference Rule ('k' Kosko, 'mk' modified Kosko, 'r' Rescale)
        if infer_rule == "k":
            x = np.matmul(AdjmT, act_vec_old)
        if infer_rule == "mk":
            x = act_vec_old + np.matmul(AdjmT, act_vec_old)
        if infer_rule == "r":
            x = (2*act_vec_old-np.ones(n)) + np.matmul(AdjmT, (2*act_vec_old-np.ones(n)))
            
        act_vec_new = TransformFunc (x ,n, f_type)
        resid = max(abs(act_vec_new - act_vec_old))
        
        act_vec_old = act_vec_new
    return act_vec_new


def infer_scenario(intervention_indexes, vals, init_vec, AdjmT, n, f_type="tanh", infer_rule="k", epsilon=0.00001):
    act_vec_old= init_vec
    
    resid = 1
    while resid > epsilon:
        act_vec_new = np.zeros(n)
        x = np.zeros(n)

        # Inference Rule ('k' Kosko, 'mk' modified Kosko, 'r' Rescale)        
        if infer_rule == "k":
            x = np.matmul(AdjmT, act_vec_old)
        if infer_rule == "mk":
            x = act_vec_old + np.matmul(AdjmT, act_vec_old)
        if infer_rule == "r":
            x = (2*act_vec_old-np.ones(n)) + np.matmul(AdjmT, (2*act_vec_old-np.ones(n)))
            
        act_vec_new = TransformFunc (x ,n, f_type)

        # reset the interventions because they are stable nodes (in-degree = 0)
        for idx, intervention_row in enumerate(intervention_indexes):
            act_vec_new[intervention_row] = vals[idx] # 1 for full activation
        
        resid = max(abs(act_vec_new - act_vec_old))
        
        act_vec_old = act_vec_new
    return act_vec_new

# Squashing Function
def TransformFunc (x, n, f_type,lamda=2):
    
    if f_type == "sig":
        x_new= 1.0/(1.0+np.exp(-lamda*x))
        return x_new 

    if f_type == "tanh":
        x_new= np.tanh(lamda*x)
        return x_new
    
    if f_type == "bivalent":
        x_new = np.zeros(n)
        for i in range (n):
            if x[i]> 0:
                x_new[i]= 1
            else:
                x_new[i]= 0
        
        return x_new
    
    if f_type == "trivalent":
        x_new = np.zeros(n)
        for i in range (n):
            if x[i]> 0:
                x_new[i] = 1
            elif x[i]==0:
                x_new[i] = 0
            else:
                x_new[i] = -1
        
        return x_new
