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

s = sampler.Sample("/my/data/dir", args={"x": 2, "y": "barbara"})
sampler.run(solve, [s])
s.result["product"] == "barbarabarbara" # yields True
```

This is useful when writing the `solve` is quickly done, but then performing it for thousands of samples, 
saving results to files, handling the IO yourself, suddenly becomes a major overhead.

## The Sample


## Storage data

```json
{
  "name": "sample-label1",
  "done": true,
  "args": {
    "length": {"value": 4},
    "grid": {"ndarray": "rel/path/to/args.npy"},
    "some_more": {
      "dict": {"x": {"value": 1}, "y": {"value": 2}}
    }
  },
  "result": {
    "time": {"value": 15.5},
    "distribution": {"ndarray": "the/distr.npy"}
  }
}
```
The filesystem is then organized as follows
```bash
name/ # samples_dir
    sample-label1/
        sample-label1.json # scalar data is here
        array-bla.npy # numpy arrays are saved in separate files
    sample-label2/
        sample-label2.json
        complex-obj.json # arbitrary objects are json-pickled
```
