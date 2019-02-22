import sys
from asgs_dataset.model.asgs_feature import ASGSFeature

def isItemAt(asgs_type, index):
    items = ASGSFeature.get_feature_index(asgs_type, index, 1)
    return len(items) == 1

def bisection(a,b,asgs_type):
    c = int((a+b)/2.0)
    while (b-a) > 1:
        print(" - {0}".format(c))
        if isItemAt(asgs_type, c):
            a = c
        else :
            b = c
        c = int((a+b)/2.0)        
		
    return a + 1 #+1 due to this being the last page that contains 1 item
	
def main(argv):
	if (len(sys.argv) < 3):
		sys.exit('Usage: find_counts.py <type> <maxGuess>')
	
	print('The count is: ')
	print(bisection(0,int(sys.argv[2]),sys.argv[1]))

if __name__ == "__main__":
	main(sys.argv[1:])