import os

for root, dirs, files in os.walk("C:/Users/NeddC/OneDrive/Documents/Degree DTS Apprenticeship/Software Engineering And Agile"):
    for file in files:
        print(os.path.join(root, file))