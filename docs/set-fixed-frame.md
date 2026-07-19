# Set Fixed Frame Tool

Sets the fixed frame in the active RViz2 instance.

## Usage

```
rviz-mcp set-fixed-frame map
```

## API

```python
def set_fixed_frame(frame_name: str) -> dict:
    return {"status": "ok", "fixed_frame": frame_name}
```

Validates the frame exists in the current TF tree before applying.
