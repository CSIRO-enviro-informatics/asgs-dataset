from os import path
import pickle
import gzip

HERE_DIR = path.dirname(__file__)
ILOC_FILE = path.join(HERE_DIR, "Indigenous_Allocations.csv")
UCL_FILE = path.join(HERE_DIR, "SA1_UCL_SOSR_SOS_2016_AUST.csv")
RA_FILE = path.join(HERE_DIR, "RA_2016_AUST.csv")
SUA_FILE = path.join(HERE_DIR, "SA2_SUA_2016_AUST.csv")

def line_reader(file):
    while True:
        line = file.readline()
        if not line:
            break
        yield line.rstrip(b'\r\n')

def row_reader(file, split_char=b','):
    l_reader = line_reader(file)
    while True:
        try:
            line = next(l_reader)  # type: bytes
        except StopIteration:
            break
        parts = line.split(split_char)
        yield [p.strip(b' ') for p in parts]

def do_sa1_to_iloc():
    sa1_to_iloc = dict()
    iloc_to_sa1 = dict()
    with open(ILOC_FILE, "rb") as f:
        reader = row_reader(f)
        headers = next(reader)
        for r in reader:
            sa1_maincode = int(r[0])
            iloc_code = int(r[1])
            if sa1_maincode in sa1_to_iloc:
                test = sa1_to_iloc[sa1_maincode]
                if test != iloc_code:
                    raise RuntimeError("An ILOC is in multiple SA1s!")
            else:
                sa1_to_iloc[sa1_maincode] = iloc_code
            if iloc_code not in iloc_to_sa1:
                iloc_to_sa1[iloc_code] = list()
            if sa1_maincode in iloc_to_sa1[iloc_code]:
                pass
            else:
                iloc_to_sa1[iloc_code].append(sa1_maincode)
    pickle_struct = {
        "sa1_to_iloc": sa1_to_iloc,
        "iloc_to_sa1": iloc_to_sa1
    }
    with open("sa1_to_iloc.pickle", "wb") as f1:
        pickle.dump(pickle_struct, f1, protocol=4)

def do_sa1_to_ucl():
    sa1_to_ucl = dict()
    ucl_to_sa1 = dict()
    with open(UCL_FILE, "rb") as f:
        reader = row_reader(f)
        headers = next(reader)
        for r in reader:
            sa1_maincode = int(r[0])
            ucl_code = int(r[2])
            if sa1_maincode in sa1_to_ucl:
                test = sa1_to_ucl[sa1_maincode]
                if test != ucl_code:
                    raise RuntimeError("A UCL is in multiple SA1s!")
            else:
                sa1_to_ucl[sa1_maincode] = ucl_code
            if ucl_code not in ucl_to_sa1:
                ucl_to_sa1[ucl_code] = list()
            if sa1_maincode in ucl_to_sa1[ucl_code]:
                pass
            else:
                ucl_to_sa1[ucl_code].append(sa1_maincode)
    pickle_struct = {
        "sa1_to_ucl": sa1_to_ucl,
        "ucl_to_sa1": ucl_to_sa1
    }
    with open("sa1_to_ucl.pickle", "wb") as f1:
        pickle.dump(pickle_struct, f1, protocol=4)

def do_sa1_to_ra():
    sa1_to_ra = dict()
    ra_to_sa1 = dict()
    with open(RA_FILE, "rb") as f:
        reader = row_reader(f)
        headers = next(reader)
        for r in reader:
            sa1_maincode = int(r[1])
            ra_code = int(r[3])
            if sa1_maincode in sa1_to_ra:
                test = sa1_to_ra[sa1_maincode]
                if test != ra_code:
                    raise RuntimeError("A RA is in multiple SA1s!")
            else:
                sa1_to_ra[sa1_maincode] = ra_code
            if ra_code not in ra_to_sa1:
                ra_to_sa1[ra_code] = list()
            if sa1_maincode in ra_to_sa1[ra_code]:
                pass
            else:
                ra_to_sa1[ra_code].append(sa1_maincode)
    pickle_struct = {
        "sa1_to_ra": sa1_to_ra,
        "ra_to_sa1": ra_to_sa1
    }
    with open("sa1_to_ra.pickle", "wb") as f1:
        pickle.dump(pickle_struct, f1, protocol=4)

def do_sa2_to_sua():
    sa2_to_sua = dict()
    sua_to_sa2 = dict()
    with open(SUA_FILE, "rb") as f:
        reader = row_reader(f)
        headers = next(reader)
        for r in reader:
            sa2_maincode = int(r[0])
            sua_code = int(r[3])
            if sa2_maincode in sa2_to_sua:
                test = sa2_to_sua[sa2_maincode]
                if test != sua_code:
                    raise RuntimeError("A SUA is in multiple SA2s!")
            else:
                sa2_to_sua[sa2_maincode] = sua_code
            if sua_code not in sua_to_sa2:
                sua_to_sa2[sua_code] = list()
            if sa2_maincode in sua_to_sa2[sua_code]:
                pass
            else:
                sua_to_sa2[sua_code].append(sa2_maincode)
    pickle_struct = {
        "sa2_to_sua": sa2_to_sua,
        "sua_to_sa2": sua_to_sa2
    }
    with open("sa2_to_sua.pickle", "wb") as f1:
        pickle.dump(pickle_struct, f1, protocol=4)

def load_sa1_to_ucl():
    with gzip.open("sa1_to_ucl.pickle.gz", "rb", compresslevel=9) as fp:
        a = pickle.load(fp)
    return a

if __name__ == "__main__":
    do_sa1_to_iloc()
    do_sa1_to_ucl()
    do_sa1_to_ra()
    do_sa2_to_sua()

# To compress these:
#$> gzip --rsyncable --best -k ./sa1_to_iloc.pickle
#$> gzip --rsyncable --best -k ./sa1_to_ucl.pickle
#$> gzip --rsyncable --best -k ./sa1_to_ra.pickle
#$> gzip --rsyncable --best -k ./sa2_to_sua.pickle
