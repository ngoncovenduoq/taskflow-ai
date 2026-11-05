
from database import (
    init_db,
    add_task,
    get_tasks,
    complete_task,
    delete_task
)


# Create database
init_db()

# Add a task
task_id = add_task("Learn SQLite")

print("Created task ID:", task_id)

# Show tasks
print("Tasks:", get_tasks())

# Mark task completed
success = complete_task(task_id)

print("Completed:", success)

# Check updated tasks
print("Updated tasks:", get_tasks())

# Delete task
deleted = delete_task(task_id)

print("Deleted:", deleted)

# Final task list
print("Final tasks:", get_tasks())
