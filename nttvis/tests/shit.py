import numpy as np
import h5py

# generate 3 random arrays of size 100
# named ex1, bx2, cx3
# save to file named "dummy.h5" using h5py
def generate_data():
    data = {}
    for i in range(3):
        data[f"ex{i+1}"] = np.random.rand(100)
    with h5py.File("dummy.h5", "w") as f:
        for k, v in data.items():
            f.create_dataset(k, data=v)
            
generate_data()