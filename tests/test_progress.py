import io
from terminal_a11y.progress import track_progress, MilestoneProgress

def test_milestone_progress_basic():
    out = io.StringIO()
    # A loop of 100 iterations emits exactly 4 lines of text.
    items = list(range(100))
    
    # Iterate through the tracked progress
    for _ in track_progress(items, file=out):
        pass
        
    output = out.getvalue().strip().split('\n')
    assert len(output) == 4
    assert output[0] == "Progress: 25%"
    assert output[1] == "Progress: 50%"
    assert output[2] == "Progress: 75%"
    assert output[3] == "Progress: 100%"

def test_milestone_progress_custom_prefix():
    out = io.StringIO()
    items = list(range(10))
    
    for _ in track_progress(items, prefix="Downloading:", file=out):
        pass
        
    output = out.getvalue().strip().split('\n')
    assert len(output) == 4
    assert output[0] == "Downloading: 25%"
    assert output[3] == "Downloading: 100%"

def test_milestone_progress_generator():
    out = io.StringIO()
    
    # Generator without explicit total won't print progress
    def gen():
        for i in range(10):
            yield i
            
    list(track_progress(gen(), file=out))
    assert out.getvalue() == ""
    
    # Generator with explicit total works
    out = io.StringIO()
    list(track_progress(gen(), total=10, file=out))
    output = out.getvalue().strip().split('\n')
    assert len(output) == 4

def test_milestone_progress_skip_milestones():
    out = io.StringIO()
    # A loop of 2 iterations
    items = list(range(2))
    
    # item 1 -> 50%
    # item 2 -> 100%
    for _ in track_progress(items, file=out):
        pass
        
    output = out.getvalue().strip().split('\n')
    assert len(output) == 4
    # It should emit 25 and 50 on the first item, and 75 and 100 on the second item.
    assert output[0] == "Progress: 25%"
    assert output[1] == "Progress: 50%"
    assert output[2] == "Progress: 75%"
    assert output[3] == "Progress: 100%"

def test_milestone_class_direct():
    out = io.StringIO()
    mp = MilestoneProgress(range(100), file=out, milestones=[50, 100])
    list(mp)
    output = out.getvalue().strip().split('\n')
    assert len(output) == 2
    assert output[0] == "Progress: 50%"
    assert output[1] == "Progress: 100%"
