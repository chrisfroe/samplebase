# Samplebase

Samplebase is a __database__, that is:
- _in-process/server-less_
- _file-local_, all data lives in a user defined path and can be moved around
- _document-based/ad-hoc_, no need to define a model beforehand
- _thread-safe_, multiple readers, one writer

The core functionality is provided by the `Sample(Document)` object. On top of that, there are a few utility methods to help with parallely processing `Samples`.

## Motivation
Let there be a task, which you can easily solve for given input arguments.
```python
result = solve(**args)
```
A `Sample` is a pair of such `args` and the corresponding `result`.
Imagine you now have thousands of different `args` that you want to sample.
__Samplebase__ enables you to separate the creation of `Samples`, from the execution of the `solve` operation and from the analysis of results.

## Example
First define the task to be executed
```python
import samplebase

def solve(x=None, y=None):
  # a lengthy calculation
  return {"product": x * y}
```
Span the space of arguments that you want to sample. Here, we have two samples.
```python
data_dir = "/my/data/dir"
samplebase.create_sample(data_dir, args={"x": 2, "y": "barbara"})
samplebase.create_sample(data_dir, args={"x": 3, "y": "og"})
```
Map the function `solve` on the samples, which are identified via their location on disk and their auto-generated names.
```python
names = samplebase.names_of_samples(data_dir)
samplebase.run_parallel(func=solve, prefix=data_dir, sample_names=names)
```
Look at results.
```python
samples = samplebase.list_of_samples(data_dir)
for s in samples:
  print(s.result["product"])
>>> barbarabarbara
>>> ogogog
```
This last part can safely be executed in another interpreter/notebook even if samples are being processed.

## Why another database?
Mostly because of parallel access with a server-less architecture. The motivation was: _Being able to look at results, while some samples are still being processed_

If this does not convince you, consider [tinydb](https://github.com/msiemens/tinydb)