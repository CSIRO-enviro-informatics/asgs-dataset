from os import path
import pickle
import gzip

HERE_DIR = path.dirname(__file__)
ILOC_FILE = path.join(HERE_DIR, "Indigenous_Allocations.csv")
UCL_FILE = path.join(HERE_DIR, "SA1_UCL_SOSR_SOS_2016_AUST.csv")
RA_FILE = path.join(HERE_DIR, "RA_2016_AUST.csv")
SUA_FILE = path.join(HERE_DIR, "SA2_SUA_2016_AUST.csv")
NRMR_FILE = path.join(HERE_DIR, "NRMR_2016_AUST.csv")
SSC_FILE = path.join(HERE_DIR, "SSC_2016_AUST.csv")
CED_FILE = path.join(HERE_DIR, "CED_2016_AUST.csv")
LGA_FILES = [
    path.join(HERE_DIR, "LGA_2016_ACT.csv"),
    path.join(HERE_DIR, "LGA_2016_NSW.csv"),
    path.join(HERE_DIR, "LGA_2016_NT.csv"),
    path.join(HERE_DIR, "LGA_2016_OT.csv"),
    path.join(HERE_DIR, "LGA_2016_QLD.csv"),
    path.join(HERE_DIR, "LGA_2016_SA.csv"),
    path.join(HERE_DIR, "LGA_2016_TAS.csv"),
    path.join(HERE_DIR, "LGA_2016_VIC.csv"),
    path.join(HERE_DIR, "LGA_2016_WA.csv"),
]

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

def do_sa1_to_ced():
    sa1_to_ced = dict()
    ced_to_sa1 = dict()
    with open(CED_FILE, "rb") as f:
        reader = row_reader(f)
        headers = next(reader)
        for r in reader:
            sa1_maincode = int(r[0])
            ced_code = int(r[1])
            if sa1_maincode in sa1_to_ced:
                test = sa1_to_ced[sa1_maincode]
                if test != ced_code:
                    raise RuntimeError("A CED is in multiple SA1s!")
            else:
                sa1_to_ced[sa1_maincode] = ced_code
            if ced_code not in ced_to_sa1:
                ced_to_sa1[ced_code] = list()
            if sa1_maincode in ced_to_sa1[ced_code]:
                pass
            else:
                ced_to_sa1[ced_code].append(sa1_maincode)
    pickle_struct = {
        "sa1_to_ced": sa1_to_ced,
        "ced_to_sa1": ced_to_sa1
    }
    with open("sa1_to_ced.pickle", "wb") as f1:
        pickle.dump(pickle_struct, f1, protocol=4)

def do_mb_to_ssc():
    mb_to_ssc = dict()
    ssc_to_mb = dict()
    with open(SSC_FILE, "rb") as f:
        reader = row_reader(f)
        headers = next(reader)
        for r in reader:
            mb_code = int(r[0])
            ssc_code = int(r[1])
            if mb_code in mb_to_ssc:
                test = mb_to_ssc[mb_code]
                if test != ssc_code:
                    raise RuntimeError("A SSC is in multiple MBs!")
            else:
                mb_to_ssc[mb_code] = ssc_code
            if ssc_code not in ssc_to_mb:
                ssc_to_mb[ssc_code] = list()
            if mb_code in ssc_to_mb[ssc_code]:
                pass
            else:
                ssc_to_mb[ssc_code].append(mb_code)
    pickle_struct = {
        "mb_to_ssc": mb_to_ssc,
        "ssc_to_mb": ssc_to_mb
    }
    with open("mb_to_ssc.pickle", "wb") as f1:
        pickle.dump(pickle_struct, f1, protocol=4)

def do_mb_to_nrmr():
    mb_to_nrmr = dict()
    nrmr_to_mb = dict()
    with open(NRMR_FILE, "rb") as f:
        reader = row_reader(f)
        headers = next(reader)
        for r in reader:
            mb_code = int(r[0])
            nrmr_code = int(r[1])
            if mb_code in mb_to_nrmr:
                test = mb_to_nrmr[mb_code]
                if test != nrmr_code:
                    raise RuntimeError("A NRMR is in multiple MBs!")
            else:
                mb_to_nrmr[mb_code] = nrmr_code
            if nrmr_code not in nrmr_to_mb:
                nrmr_to_mb[nrmr_code] = list()
            if mb_code in nrmr_to_mb[nrmr_code]:
                pass
            else:
                nrmr_to_mb[nrmr_code].append(mb_code)
    pickle_struct = {
        "mb_to_nrmr": mb_to_nrmr,
        "nrmr_to_mb": nrmr_to_mb
    }
    with open("mb_to_nrmr.pickle", "wb") as f1:
        pickle.dump(pickle_struct, f1, protocol=4)

def do_mb_to_lga():
    mb_to_lga = dict()
    lga_to_mb = dict()
    for LF in LGA_FILES:
        with open(LF, "rb") as f:
            reader = row_reader(f)
            headers = next(reader)
            for r in reader:
                mb_code = int(r[0])
                nrmr_code = int(r[1])
                if mb_code in mb_to_lga:
                    test = mb_to_lga[mb_code]
                    if test != nrmr_code:
                        raise RuntimeError("A LGA is in multiple MBs!")
                else:
                    mb_to_lga[mb_code] = nrmr_code
                if nrmr_code not in lga_to_mb:
                    lga_to_mb[nrmr_code] = list()
                if mb_code in lga_to_mb[nrmr_code]:
                    pass
                else:
                    lga_to_mb[nrmr_code].append(mb_code)
    pickle_struct = {
        "mb_to_lga": mb_to_lga,
        "lga_to_mb": lga_to_mb
    }
    with open("mb_to_lga.pickle", "wb") as f1:
        pickle.dump(pickle_struct, f1, protocol=4)

def load_sa1_to_ucl():
    with gzip.open("sa1_to_ucl.pickle.gz", "rb", compresslevel=9) as fp:
        a = pickle.load(fp)
    return a

if __name__ == "__main__":
    # do_sa1_to_iloc()
    # do_sa1_to_ucl()
    # do_sa1_to_ra()
    # do_sa2_to_sua()
    # do_sa1_to_ced()
    # do_mb_to_ssc()
    # do_mb_to_nrmr()
    do_mb_to_lga()

# To compress these:
#$> gzip --rsyncable --best -k ./sa1_to_iloc.pickle
#$> gzip --rsyncable --best -k ./sa1_to_ucl.pickle
#$> gzip --rsyncable --best -k ./sa1_to_ra.pickle
#$> gzip --rsyncable --best -k ./sa2_to_sua.pickle
