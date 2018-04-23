import json
class lookerTable:
    ''' A Data or HTML redering of Json_detail from Looker '''
    class measure:
        __slots__ = [
             'description'
            ,'label'
            ,'label_short'
            ,'type'
            ,'name'
            ,'hidden'
        ]
        def __init__(self,*args,**kwargs):
            self.description = kwargs.get('description',None)
            self.label = kwargs.get('label',None)
            self.label_short = kwargs.get('label_short',None)
            self.type = kwargs.get('type',None)
            self.name = kwargs.get('name',None)
            self.hidden = kwargs.get('hidden',None)

    class dimension:
        __slots__ = [
             'description'
            ,'label'
            ,'label_short'
            ,'type'
            ,'name'
            ,'hidden'
        ]
        def __init__(self,*args,**kwargs):
            self.description = kwargs.get('description',None)
            self.label       = kwargs.get('label',None)
            self.label_short = kwargs.get('label_short',None)
            self.type        = kwargs.get('type',None)
            self.name        = kwargs.get('name',None)
            self.hidden      = kwargs.get('hidden',None)

    class tableCalc:
        __slots__ = [
             'description'
            ,'label'
            ,'label_short'
            ,'type'
            ,'name'
            ,'hidden'
            ,'can_pivot'
        ]
        def __init__(self,*args,**kwargs):
            self.description = kwargs.get('description',None)
            self.label = kwargs.get('label',None)
            self.label_short = kwargs.get('label_short',None)
            self.type = kwargs.get('type',None)
            self.name = kwargs.get('name',None)
            self.hidden = kwargs.get('hidden',None)
            self.can_pivot = kwargs.get('can_pivot',None)

    class pivot:
        __slots__ = [
             'key'
            ,'data'
        ]
        def __init__(self,*args,**kwargs):
            self.key = kwargs.get('key',None)
            self.data = kwargs.get('data',None)

    def __init__(self,*args,**kwargs):
        ''' Take Json_detail as a constructor '''
        if 'raw' in kwargs.keys():
            self.raw = json.loads(kwargs.get('raw'))
        elif 'json_detail' in kwargs.keys():
            self.raw = kwargs.get('json_detail',None)
        else:
            pass
        self.pivots = [self.pivot(**pivot) for pivot in self.raw['pivots']] if 'pivots' in self.raw.keys() else None
        self.measures = [self.measure(**meas) for meas in self.raw['fields']['measures']] if 'measures' in self.raw['fields'].keys() else None
        self.dimensions = [self.dimension(**dim) for dim in self.raw['fields']['dimensions']] if 'dimensions' in self.raw['fields'].keys() else None
        self.calculations = [self.tableCalc(**calc) for calc in self.raw['fields']['table_calculations']] if 'table_calculations' in self.raw['fields'].keys() else None
        self.dimCalculations = list(filter(lambda x: not x.can_pivot, self.calculations))
        self.measCalculations = list(filter(lambda x: x.can_pivot, self.calculations))
        self.dimWidth = len(self.dimensions) + len(self.dimCalculations)
        self.measWidth = len(self.measures) + len(self.measCalculations)


    def transposePivot(self):
        self.pivot_fields = self.pivots[0].data.keys()
        pivRow = []
        for field in self.pivot_fields:
            pivRow.append(field)
            for pivot in self.pivots:
                pivRow.append(pivot.data[field])
            yield pivRow
            pivRow = []

    def pivotHeader(self):
        if self.pivots:
            for row in self.transposePivot():
                yield row

    def header(self):
        headerRow = []
        for dim in self.dimensions:
             headerRow.append(dim.label_short)
        for dimCalc in self.dimCalculations:
             headerRow.append(dimCalc.label)
        if self.pivots:
            for pivot in self.pivots:
                for meas in self.measures:
                    headerRow.append(meas.label_short)
                for calc in self.measCalculations:
                    headerRow.append(calc.label)
        else:
            for meas in self.measures:
                headerRow.append(meas.label_short)
            for calc in self.measCalculations:
                headerRow.append(calc.label)
        yield headerRow
            

    def rows(self):
        def rowData(rw,key,piv=None):
            if piv:
                return rw[key][piv]['rendered'] if 'rendered' in row[key][piv].keys() else row[key][piv]['value']
            else:    
                return rw[key]['rendered'] if 'rendered' in rw[key].keys() else rw[key]['value']

        for row in self.raw['data']:
            tmpRow = []
            for dim in self.dimensions:
                tmpRow.append(rowData(row,dim.name))
            for dimCal in self.dimCalculations:
                tmpRow.append(rowData(row,dimCal.name))
            if self.pivots:
                for pivot in self.pivots:
                    for meas in self.measures:
                        tmpRow.append(rowData(row,meas.name,piv=pivot.key))
                    for tablecalc in self.measCalculations:
                        tmpRow.append(rowData(row,tablecalc.name,piv=pivot.key))
            else:
                for meas in self.measures:
                    tmpRow.append(rowData(row,meas.name))
                for tablecalc in self.measCalculations:
                    tmpRow.append(rowData(row,tablecalc.name))
            
            yield tmpRow

    def asHTML(self,theme='blueTable'):
        returnString = '<table class="{}" >'.format(theme)
        for row in self.pivotHeader():
            returnString = returnString + \
            '\n<thead> \n\t<th colspan="' + str(self.dimWidth) + '">' +\
            row[0] + '</th> \n\t<th colspan="' + str(self.measWidth) + '">' +\
            f'</th> \n<th colspan="{self.measWidth}">'.join(row[1:])+'</th> </thead>'
        for row in self.header():
            returnString = returnString + '\n<thead> \n\t<th>' + '</th> \n<th>'.join(row)+'</th> </thead>'
        returnString = returnString + '\n<body>'
        for row in self.rows():
            returnString = returnString + '\n\t <tr> <td>' + '</td> <td>'.join([str(i) for i in row])+'</td> </tr>'
        returnString = returnString + '\n</body>'
        returnString = returnString + '\n</table>'
        return returnString