import h5py, numpy as np

x = np.linspace(-2, 2, 256)
y = np.linspace(-2, 2, 256)
x, y = np.meshgrid(x, y)

for t in range(10):
    arr1 = x + 0.5 * y - np.tanh(x * y * t)
    arr2 = np.sin(t * x) - np.cos((12 - t) * y)
    
    with h5py.File(f'dummy{t:02d}.hdf5', 'w') as f:
        f.create_dataset('arr1', data=arr1)
        f.create_dataset('arr2', data=arr2)
