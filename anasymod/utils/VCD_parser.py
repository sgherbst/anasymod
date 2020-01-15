
__all__ = ["ParseVCD"]

class ParseVCD:
    def __init__(self, vcd_root):
        self.vcd_root = vcd_root
        self.cycle_value = 'cv'

    def parse_vcd(self, sig_names=0, stdout=0, sigs=[], update_data=False):
        #Initialization
        usigs = {}
        data = {}
        hierarchy = []
        cycle_cnt = 0
        
        for i in sigs:
            usigs[i] = 1

        if len(usigs):
            all_sigs = 0
        else:
            all_sigs = 1

        with open(self.vcd_root, 'r') as file:
            while True:
                line = file.readline()
                if line == '':  # End-of-File
                    self.update_data(cycle_cnt=cycle_cnt, data=data)
                    break
                line = line.strip()

                if line == '':
                    continue

                if line[0] in ('r', 'R', 'b', 'B'):
                    (value, code) = line[1:].split()
                    try:
                        #convert all x and z to 0
                        if line[0] in ('b', 'B'):
                            value = value.replace('x', '0').replace('z', '0')
                        else:
                            value = float(value)
                    except:
                        # This is a quick fix that sets X,Z, ... to 0
                        value = float(0)
                    if (code in data):
                        if (stdout):
                            print(cycle_cnt, value)
                        else:
                            if self.cycle_value not in data[code]:
                                data[code][self.cycle_value] = []
                            data[code][self.cycle_value].append((cycle_cnt, value))

                elif line[0] in ('x', 'X', 'z', 'Z', '0', '1'):
                    value = line[0]
                    code = line[1:]
                    if (code in data):
                        if (stdout):
                            print(cycle_cnt, value)
                        else:
                            if self.cycle_value not in data[code]:
                                data[code][self.cycle_value] = []
                            data[code][self.cycle_value].append((cycle_cnt, value))

                elif line[0] == '#':
                    if update_data: self.update_data(cycle_cnt=cycle_cnt, data=data)
                    cycle_cnt = int(line[1:])

                elif "$enddefinitions" in line:
                    num_sigs = len(data)
                    if (num_sigs == 0):
                        if (all_sigs):
                            raise Exception(f"No signals were found reading VCD file {self.vcd_root}")
                        else:
                            raise Exception(f"No matching signals were found reading VCD file: {self.vcd_root}")
                    if ((num_sigs > 1) and stdout):
                        raise Exception("Too many signals provided to VCD parser!")
                    if sig_names:
                        break

                elif "$scope" in line:
                    hierarchy.append(line.split()[2])

                elif "$upscope" in line:
                    hierarchy.pop()

                elif "$var" in line:
                    ls = line.split()
                    type = ls[1]
                    size = ls[2]
                    code = ls[3]

                    name = ls[4]
                    path = '.'.join(hierarchy)
                    full_name = path + '.' + name
                    if (full_name in usigs) or all_sigs:
                        if code not in data:
                            data[code] = {}
                        if 'nets' not in data[code]:
                            data[code]['nets'] = []
                        var_struct = {
                            'type': type,
                            'name': name,
                            'size': size,
                            'hier': path,
                        }
                        if var_struct not in data[code]['nets']:
                            data[code]['nets'].append(var_struct)

        file.close()

        return data
    
    def update_data(self, cycle_cnt, data):
        if cycle_cnt != 0:
            cycle_cnt_old = cycle_cnt
            for d in data.keys():
                length = len(data[d][self.cycle_value]) - 1
                if data[d][self.cycle_value][length][0] != cycle_cnt_old:
                    data[d][self.cycle_value].append((cycle_cnt_old, data[d][self.cycle_value][length][1]))

    def list_sigs(self):

        vcd = self.parse_vcd(sig_names=1)

        sigs = []
        for k in vcd.keys():
            v = vcd[k]
            nets = v['nets']
            sigs.extend(n['hier'] + '.' + n['name'] for n in nets)

        return sigs
