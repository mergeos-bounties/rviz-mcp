# Remote API Bridge for RViz2

## Overview

The Remote API Bridge provides a way to control RViz2 displays, fixed frames, and views remotely. It includes both a live implementation and a mock version for CI and testing purposes.

## Configuration

The bridge can be configured using the `Config` class in `src/config.py`. Key configuration options include:

- `remote_api_url`: URL of the remote RViz2 API
- `timeout`: Connection timeout in seconds
- `retry_attempts`: Number of retry attempts for failed connections

## Usage

### Live Implementation