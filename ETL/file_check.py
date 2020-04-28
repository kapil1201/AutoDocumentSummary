import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from Pandas_ETL import load_forecast_pandas

def on_change(event):
    print(event.src_path)
    obj=load_forecast_pandas(event.src_path)
    obj.main()

def on_created(event):
    on_change(event)
    
    
if __name__ == "__main__":
    patterns = "*"
    ignore_patterns = ""
    ignore_directories = False
    case_sensitive = True
    my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
    my_event_handler.on_created = on_created
    
    path = r"D:\BYOM\ETL\files"
    go_recursively = True
    my_observer = Observer()
    my_observer.schedule(my_event_handler, path, recursive=go_recursively)
    
    my_observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        my_observer.stop()
        my_observer.join()