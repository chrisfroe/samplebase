# Sampler
Let there be a task, which you can easily solve for a given set of input arguments.
```python
result = solve(**args)
```
Sampler performs this task for a list of samples, one sample consists of one`args` and the corresponding `result`.
```python
import sampler

def solve(x=None, y=None):
  # a lengthy calculation
  return {"product": x * y}

s = sampler.Sampler("foo", prefix="/my/data/dir", solve)
s.add({"x": 2, "y": "barbara"}, "myfirstsample")
s.sample()
s.result("myfirstsample")["product"] == "barbarabarbara" # yields True
```

Sampler performs these tasks using multiple threads, saving the results to files, organized according to 
the [specification](#specification) and provides access to the samples' arguments and results.

This is useful when writing the `solve` is quickly done, but then performing it for thousands of samples, 
saving results to files, handling the IO yourself, suddenly becomes a major overhead.

## Specification

Each sample has its own file. This allows moving samples from one sampler to another if data 
shall be reused there, or move it to another machine, without having to copy the whole data-tree.
An example for a `sample-label1.json` is
```json
{
  "name": "sample-label1", // a unique string
  "done": true, // has been sampled?
  "args": {
    // an arg has either value or points to a file
    "length": {"value": 4},
    "grid": {"file": "rel/path/to/args.npz"},
    ...
  },
  "result": {
    "time": {"value": 15.5},
    "distribution": {"file": "the/distr.npy"},
    ...
  }
}
```
Another sample might have the following `sample-label2.json`. It contains no result yet.
```json
{
  "name": "sample-label2",
  "done": false,
  "args": {
    "length": {"value": 1},
    ...
  }
}
```
The filesystem is then organized as follows
```bash
prefix/
  name/ # samples_dir
    sample-label1/
      sample-label1.json # scalar data is here
      args/
        # array data goes here
      result/
        # array data goes here
    sample-label2/
      sample-label2.json
      args/
      result/
```

A sample is represented on the filesystem by its directory, which is why its name must be unique. 
Trying to add a sample with an already existing name should raise an error.

The state of a particular Sampler itself persists without a runtime. Its state 
can always be reconstructed from the filesystem under `prefix`, that can be loaded when 
constructing another Sampler object.