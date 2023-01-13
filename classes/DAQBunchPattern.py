import os
from datetime import datetime
from struct import pack, unpack
import numpy as np
import classes.DAQbasic as dqb

SASE_info = {'FLASH':[{'Bits':list(range(0,4)), 'Name':'Charge', 'Op':'Abs', 
                    'Value':{'0':0, '1':0.02, '2':0.03, '3':0.04,
                            '4':0.06, '5':0.09, '6':0.13, '7':0.18,
                            '8':0.25, '9':0.36, '10':0.50, '11':0.71, 
                            '12':1.00, '13':1.42, '14':2.00, '15':4.00}},
                    {'Bits':list(range(4,8)), 'Name':'Injector Laser', 'Op':'Bits',
                    'Value':{'4':'Laser1', '5':'Laser2', '6':'Laser3', '7':'Laser4'}}, 
                    {'Bits':list(range(8,14)), 'Name':'User Laser', 'Op':'Bits',
                    'Value':{'8':'Seed1',
                             '9':'Seed2',
                             '10':'Seed3',
                             '11':'PP1',
                             '12':'PP2',
                             '13':'PP3'}},
                    {'Bits':list(range(14,18)), 'Name':'Not used', 'Op':'Bits',
                    'Value':{'14':'Not used bit 14',
                             '15':'Not used bit 15',
                             '16':'Not used bit 16',
                             '17':'Not used bit 17'}},
                    {'Bits':list(range(18,22)), 'Name':'Destination', 'Op':'Abs',
                    'Value':{'0':'None',
                             '1':'LSt (Laser stand-alone)',
                             '2':'FL2D (FLASH2 dump)',
                             '3':'GnD (Gun dump/IDUMP)',
                             '4':'FL1D (FLASH1 dump)',
                             '5':'Not used value 5',
                             '6':'Not used value 6',
                             '7':'Not used value 7',
                             '8':'FFwD (FLASH3 dump)' }},
                    {'Bits':list(range(22,23)), 'Name':'Event trigger 25', 'Op':'Bits',
                    'Value':{'22':'Reduced rep rate' }},
                    {'Bits':list(range(23,27)), 'Name':'Not used', 'Op':'Bits',
                    'Value':{'23':'Not used bit 23',
                            '24':'Not used bit 24',
                            '25':'Not used bit 25',
                            '26':'Not used bit 26' }},
                    {'Bits':list(range(27,32)), 'Name':'Special Flags', 'Op':'Bits',
                    'Value':{'27':'Photon mirror',
                             '28':'Wire scanner',
                             '29':'LOLA',
                             '30':'CRISP kicker',
                             '31':'Undefined bit 31'}}],
                'XFEL':[{'Bits':list(range(0,4)), 'Name':'Charge', 'Op':'Abs', 
                    'Value':{'0':0, '1':0.02, '2':0.03, '3':0.04,
                            '4':0.06, '5':0.09, '6':0.13, '7':0.18,
                            '8':0.25, '9':0.36, '10':0.50, '11':0.71, 
                            '12':1.00, '13':1.42, '14':2.00, '15':4.00}},
                    {'Bits':list(range(4,8)), 'Name':'Injector Laser', 'Op':'Bits',
                    'Value':{'4':'I1.Laser1', '5':'I1.Laser2', '6':'I1.Laser3', '7':'I2.Laser1'}}, 
                    {'Bits':list(range(8,17)), 'Name':'Seed/user Laser', 'Op':'Bits',
                    'Value':{'8':'Seed/user Laser1',
                             '9':'Seed/user Laser2',
                             '10':'Seed/user Laser3',
                             '11':'Seed/user Laser4',
                             '12':'Seed/user Laser5',
                             '13':'Seed/user Laser6',
                             '14':'Seed/user Laser7',
                             '15':'Seed/user Laser8',
                             '16':'Seed/user Laser9'}},
                    {'Bits':list(range(18,22)), 'Name':'Destination', 'Op':'Abs',
                    'Value':{'0':'None',
                             '1':'I1lSt (Laser stand-alone)',
                             '2':'T5D (SASE2 dump)',
                             '3':'G1D (Gun dump/valve)',
                             '4':'T4D (SASE1/3 dump)',
                             '5':'I1D (Injector dump)',
                             '6':'B1D (B1 dump)',
                             '7':'B2D (B2 dump)',
                             '8':'TLD' }},
                    {'Bits':list(range(22,25)), 'Name':'Not used', 'Op':'Bits',
                    'Value':{'22':'Not used bit 22',
                            '23':'Not used bit 23',
                            '24':'Not used bit 24' }},
                    {'Bits':list(range(25,32)), 'Name':'Special Flags', 'Op':'Bits',
                    'Value':{'25':'SASE3 soft kick (T4)',
                             '26':'Beam distribution kicker (T1)',
                             '27':'Soft kick (e.g.SA3)',
                             '28':'Wire scanner',
                             '29':'TDS BC2',
                             '30':'TDS BC1', 
                             '31':'TDS Inj'}}]
            }
                

class  DAQBunchPattern:
    
    def __init__(self, linac='XFEL'):
        # constants for Scan Mode
        self.linacs = SASE_info.keys()
        self.linac = None
        self.bunch_info = None
        list_out = []
        for lin in  self.linacs:
            linc = linac.upper()
            list_out.append(lin)    
            if linc == lin:
                self.bunch_info = SASE_info[lin]
                self.linac = linc
        if not  self.bunch_info:
            out = "Unknown LINAC name " + linac + ' (must be one of'
            for l in list_out:
                out += ' ' + l
            out += ')'
            raise Exception(out)


    def get_names_of_all_linac(self):
        out = []
        for entry in self.linacs:
            out.append(entry)
        return out

    def print_all_patterns(self):
        print('LINAC->%s'%self.linac)
        for entry in self.bunch_info:
            print('\t%s:'% entry['Name'].strip('"\''), end='')
            for val in entry['Value'].values():
                print('\n\t\t%s'% str(val).strip('"\''), end='')
            print()
    
    def get_bunch_pattern_info(self, mode, debug):
        if isinstance(mode, int):
            pass
        elif isinstance(mode, float) or isinstance(mode, np.float32):
            mode = dqb.float2int(mode)
        else:
            raise Exception("Invalid data type %s (must be int or float) "%(type(mode)))
            
        result = []
        if debug: print('mode: 0x%X'%mode)
        for entry in self.bunch_info:
            bits =  entry['Bits']
            op = entry['Op']
            name = entry['Name']
            values= entry['Value']
            mask = (2**(len(bits))) - 1
            shift = bits[0]
            if debug: print('Name: %s Op:%s Bits Total: %d Shift:%d Mask:%d'%(name, op, len(bits), shift, mask))
            if op == 'Abs':
                rest = (mode>>shift) & mask
                for val in values.keys():
                    if int(val) == rest:
                        if debug : print('%s -> %s '%(name, values[val]))
                        result.append({name:values[val]})    
                        break
            if op == 'Bits':
                out = []
                for val in values.keys():
                    if 1<<int(val) & mode:
                        #print('Comparing 0x%X 0x%X'%(1<<int(val), mode))
                        if debug : print('%s -> %s '%(name, values[val]))
                        result.append({name:values[val]})

                #if out != []:
                #    if debug: print('%s -> '%(name), out)
                #    result.append(out)   
        if debug: print('result:', result)
        return result

    def check_bunch_pattern(self, value, pattern, logic, debug):
        if not isinstance(pattern, list): 
            raise Exception("Invalid data type %s (must be list) "(type(pattern)))
        res = self.get_bunch_pattern_info(value, debug)
        if pattern == []: return True, res
        found = 0
        for item in pattern:
            for entry in res:
                ks = item.keys()
                for t in ks:
                    if t in entry and  (entry[t] == item[t]):
                        found += 1

        if logic == 'AND' and found == len(pattern): return True, res
        if logic == 'OR' and found: return True, res
        return False, res
