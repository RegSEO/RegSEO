import pandas as pd
import random

class LabelWriter:
    def __init__(self):
        pass

    def write_black_labels_to_excel(self, filename):
        names = []
        with open("./true_black_name.txt",'r') as black_f:
            for line in black_f:
                names.append(line.rstrip('\n'))
        names2 = []
        with open("./abuse2.txt",'r') as black_f:
            for line in black_f:
                names2.append(line.rstrip('\n'))        
        a = random.sample(names, 5000)
        b = random.sample(names2, 5000)
        c = a+b
        df = pd.DataFrame(c, columns=["name"])
        df["label"] = 1
        df.to_excel(filename, index=False)
        
    def write_white_labels_to_excel(self, filename):
        names = []
        _count=0
        with open("./true_white_name.txt",'r') as white_f:
            for line in white_f:
                names.append(line.rstrip('\n'))
                
        b = random.sample(names, 10000)
                
        
        df = pd.DataFrame(b, columns=["name"])
        df["label"] = 0
        df.to_excel(filename, index=False)


if __name__ == "__main__":
    label_writer = LabelWriter()
    label_writer.write_black_labels_to_excel("test_lable_black_v3.xlsx")
    # label_writer.write_white_labels_to_excel("test_lable_white_v3.xlsx")
