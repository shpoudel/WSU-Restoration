# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 11:17:12 2019

@author: spoudel
"""

class MODEL_EQ(object):
    """
    WSU Resilient Restoration. Mapping Switch MRIDs
    """
    def __init__(self, gapps, model_mrid, topic):
        self.gapps = gapps
        self.model_mrid = model_mrid
        self.topic = topic
        
    def get_switches_mrids(self):
        query = """
    PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c:  <http://iec.ch/TC57/CIM100#>
    SELECT ?cimtype ?name ?bus1 ?bus2 ?id WHERE {
    SELECT ?cimtype ?name ?bus1 ?bus2 ?phs ?id WHERE {
    VALUES ?fdrid {"%s"}  # 9500 node
    VALUES ?cimraw {c:LoadBreakSwitch c:Recloser c:Breaker}
    ?fdr c:IdentifiedObject.mRID ?fdrid.
    ?s r:type ?cimraw.
    bind(strafter(str(?cimraw),"#") as ?cimtype)
    ?s c:Equipment.EquipmentContainer ?fdr.
    ?s c:IdentifiedObject.name ?name.
    ?s c:IdentifiedObject.mRID ?id.
    ?t1 c:Terminal.ConductingEquipment ?s.
    ?t1 c:ACDCTerminal.sequenceNumber "1".
    ?t1 c:Terminal.ConnectivityNode ?cn1. 
    ?cn1 c:IdentifiedObject.name ?bus1.
    ?t2 c:Terminal.ConductingEquipment ?s.
    ?t2 c:ACDCTerminal.sequenceNumber "2".
    ?t2 c:Terminal.ConnectivityNode ?cn2. 
    ?cn2 c:IdentifiedObject.name ?bus2
        OPTIONAL {?swp c:SwitchPhase.Switch ?s.
        ?swp c:SwitchPhase.phaseSide1 ?phsraw.
        bind(strafter(str(?phsraw),"SinglePhaseKind.") as ?phs) }
    } ORDER BY ?name ?phs
    }
    GROUP BY ?cimtype ?name ?bus1 ?bus2 ?id
    ORDER BY ?cimtype ?name
        """ % self.model_mrid
        results = self.gapps.query_data(query, timeout=60)
        results_obj = results['data']
        switches = []
        for p in results_obj['results']['bindings']:
            sw_mrid = p['id']['value']
            fr_to = [p['bus1']['value'].upper(), p['bus2']['value'].upper()]
            message = dict(name = p['name']['value'],
                        mrid = sw_mrid,
                        sw_con = fr_to)
            switches.append(message) 
        print('switches..')
        return switches

    def meas_mrids(self):

        # Get measurement MRIDS for LoadBreakSwitches
        message = {
        "modelId": self.model_mrid,
        "requestType": "QUERY_OBJECT_MEASUREMENTS",
        "resultFormat": "JSON",
        "objectType": "LoadBreakSwitch"}     
        obj_msr_loadsw = self.gapps.get_response(self.topic, message, timeout=180)   

        # Get measurement MRIDS for kW consumptions at each node
        message = {
            "modelId": self.model_mrid,
            "requestType": "QUERY_OBJECT_MEASUREMENTS",
            "resultFormat": "JSON",
            "objectType": "EnergyConsumer"}     
        obj_msr_demand = self.gapps.get_response(self.topic, message, timeout=180)
        print('Gathering Measurement MRIDS.... \n')
        return obj_msr_loadsw, obj_msr_demand
    

    def distLoad(self):
        query = """
    PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c:  <http://iec.ch/TC57/CIM100#>
    SELECT ?name ?bus ?basev ?p ?q ?conn ?cnt ?pz ?qz ?pi ?qi ?pp ?qp ?pe ?qe ?fdrid WHERE {
    ?s r:type c:EnergyConsumer.
    # feeder selection options - if all commented out, query matches all feeders
    VALUES ?fdrid {"%s"}  # R2 12.47 3
    ?s c:Equipment.EquipmentContainer ?fdr.
    ?fdr c:IdentifiedObject.mRID ?fdrid.
    ?s c:IdentifiedObject.name ?name.
    ?s c:ConductingEquipment.BaseVoltage ?bv.
    ?bv c:BaseVoltage.nominalVoltage ?basev.
    ?s c:EnergyConsumer.customerCount ?cnt.
    ?s c:EnergyConsumer.p ?p.
    ?s c:EnergyConsumer.q ?q.
    ?s c:EnergyConsumer.phaseConnection ?connraw.
    bind(strafter(str(?connraw),"PhaseShuntConnectionKind.") as ?conn)
    ?s c:EnergyConsumer.LoadResponse ?lr.
    ?lr c:LoadResponseCharacteristic.pConstantImpedance ?pz.
    ?lr c:LoadResponseCharacteristic.qConstantImpedance ?qz.
    ?lr c:LoadResponseCharacteristic.pConstantCurrent ?pi.
    ?lr c:LoadResponseCharacteristic.qConstantCurrent ?qi.
    ?lr c:LoadResponseCharacteristic.pConstantPower ?pp.
    ?lr c:LoadResponseCharacteristic.qConstantPower ?qp.
    ?lr c:LoadResponseCharacteristic.pVoltageExponent ?pe.
    ?lr c:LoadResponseCharacteristic.qVoltageExponent ?qe.
    OPTIONAL {?ecp c:EnergyConsumerPhase.EnergyConsumer ?s.
    ?ecp c:EnergyConsumerPhase.phase ?phsraw.
    bind(strafter(str(?phsraw),"SinglePhaseKind.") as ?phs) }
    ?t c:Terminal.ConductingEquipment ?s.
    ?t c:Terminal.ConnectivityNode ?cn. 
    ?cn c:IdentifiedObject.name ?bus
    }
    GROUP BY ?name ?bus ?basev ?p ?q ?cnt ?conn ?pz ?qz ?pi ?qi ?pp ?qp ?pe ?qe ?fdrid
    ORDER by ?name
        """ % self.model_mrid
        results = self.gapps.query_data(query, timeout=60)
        results_obj = results['data']
        LoadData = []
        demand = results_obj['results']['bindings']
        for ld in demand:
            name = ld['bus']['value']
            message = dict(bus = ld['bus']['value'],
                        Phase  = name[-1].upper(),
                        kW = 0.001 *  float (ld['p']['value']),
                        kVaR = 0.001 * float(ld['q']['value']))
            LoadData.append(message)   
        print('Load..')
        # sP = 0.
        # sQ = 0.
        # for l in LoadData:
        #     sP += 0.001 * float(l['kW'])
        #     sQ += 0.001 * float(l['kVAR'])

        # print(sP, sQ)


        query = """
    PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c:  <http://iec.ch/TC57/CIM100#>
    SELECT ?pname ?tname ?xfmrcode ?vgrp ?enum ?bus ?basev ?phs ?grounded ?rground ?xground ?fdrid WHERE {
    ?p r:type c:PowerTransformer.
    # feeder selection options - if all commented out, query matches all feeders
    #VALUES ?fdrid {"_C1C3E687-6FFD-C753-582B-632A27E28507"}  # 123 bus
    #VALUES ?fdrid {"_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62"}  # 13 bus
    #VALUES ?fdrid {"_5B816B93-7A5F-B64C-8460-47C17D6E4B0F"}  # 13 bus assets
    #VALUES ?fdrid {"_4F76A5F9-271D-9EB8-5E31-AA362D86F2C3"}  # 8500 node
    #VALUES ?fdrid {"_67AB291F-DCCD-31B7-B499-338206B9828F"}  # J1
    #VALUES ?fdrid {"_9CE150A8-8CC5-A0F9-B67E-BBD8C79D3095"}  # R2 12.47 3
    #VALUES ?fdrid {"_E407CBB6-8C8D-9BC9-589C-AB83FBF0826D"}  # 123 PV/Triplex
    VALUES ?fdrid {"%s"}  # 9500 node
    ?p c:Equipment.EquipmentContainer ?fdr.
    ?fdr c:IdentifiedObject.mRID ?fdrid.
    ?p c:IdentifiedObject.name ?pname.
    ?p c:PowerTransformer.vectorGroup ?vgrp.
    ?t c:TransformerTank.PowerTransformer ?p.
    ?t c:IdentifiedObject.name ?tname.
    ?asset c:Asset.PowerSystemResources ?t.
    ?asset c:Asset.AssetInfo ?inf.
    ?inf c:IdentifiedObject.name ?xfmrcode.
    ?end c:TransformerTankEnd.TransformerTank ?t.
    ?end c:TransformerTankEnd.phases ?phsraw.
    bind(strafter(str(?phsraw),"PhaseCode.") as ?phs)
    ?end c:TransformerEnd.endNumber ?enum.
    ?end c:TransformerEnd.grounded ?grounded.
    OPTIONAL {?end c:TransformerEnd.rground ?rground.}
    OPTIONAL {?end c:TransformerEnd.xground ?xground.}
    ?end c:TransformerEnd.Terminal ?trm.
    ?trm c:Terminal.ConnectivityNode ?cn. 
    ?cn c:IdentifiedObject.name ?bus.
    ?end c:TransformerEnd.BaseVoltage ?bv.
    ?bv c:BaseVoltage.nominalVoltage ?basev
    }
    ORDER BY ?pname ?tname ?enum
        """ % self.model_mrid
        results = self.gapps.query_data(query, timeout=60)
        results_obj = results['data']
        Xfmr = []
        trans = results_obj['results']['bindings']
        xtr = [tr for tr in trans if tr['vgrp']['value'] != 'Ii']
        for i, t in enumerate(xtr):
            if i % 3 == 0:
                trn = xtr[i]
                b = xtr[i+1]
                message = dict(name = trn['pname']['value'],
                            bus1 = trn['bus']['value'],
                            bus2 = b['bus']['value'])
            Xfmr.append(message)   
        print('Xfm.. \n')
        # Now transferring load into primary using XFMR connectivity
        for ld in LoadData:
            node = ld['bus'].strip('s')
            # Find this node in Xfrm to_br
            for tr in Xfmr:
                sec = tr['bus2']
                if sec == node:
                    # Transfer this load to primary and change the node name
                    ld['bus'] = tr['bus1'].upper()

        # sP = 0.
        # sQ = 0.
        # for l in LoadData:
        #     sP += 0.001 * float(l['kW'])
        #     sQ += 0.001 * float(l['kVAR'])       
        
        # print(LoadData)
        # print(sP, sQ)
        # # print (Xfmr)
        return LoadData, Xfmr


    def Inverters(self):
        query = """
    PREFIX r: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c: <http://iec.ch/TC57/CIM100#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT ?inverter_mrid ?inverter_name ?inverter_mode ?inverter_max_q ?inverter_min_q ?inverter_p ?inverter_q ?inverter_rated_s ?inverter_rated_u ?phase_mrid ?phase_name ?phase_p ?phase_q 
    WHERE {
    # Update for your feeder, or remove for all feeders.
    VALUES ?feeder_mrid {"%s"}
    ?s r:type c:PowerElectronicsConnection.
    ?s c:Equipment.EquipmentContainer ?fdr.
    ?fdr c:IdentifiedObject.mRID ?feeder_mrid.
    ?s c:IdentifiedObject.mRID ?inverter_mrid.
    ?s c:IdentifiedObject.name ?inverter_name.
    ?s c:PowerElectronicsConnection.p ?inverter_p.
    ?s c:PowerElectronicsConnection.q ?inverter_q.
    ?s c:PowerElectronicsConnection.ratedS ?inverter_rated_s.
    ?s c:PowerElectronicsConnection.ratedU ?inverter_rated_u.
    OPTIONAL {
    ?s c:PowerElectronicsConnection.inverterMode ?inverter_mode.
    ?s c:PowerElectronicsConnection.maxQ ?inverter_max_q.
    ?s c:PowerElectronicsConnection.minQ ?inverter_min_q.
    }
    OPTIONAL {
    ?pecp c:PowerElectronicsConnectionPhase.PowerElectronicsConnection ?s.
    ?pecp c:IdentifiedObject.mRID ?phase_mrid.
    ?pecp c:IdentifiedObject.name ?phase_name.
    ?pecp c:PowerElectronicsConnectionPhase.p ?phase_p.
    ?pecp c:PowerElectronicsConnectionPhase.q ?phase_q.
    ?pecp c:PowerElectronicsConnectionPhase.phase
    ?phsraw bind(strafter(str(?phsraw),"SinglePhaseKind.") as ?phs)
    }
    }
    GROUP BY ?inverter_mrid ?inverter_name ?inverter_rated_s ?inverter_rated_u ?inverter_p ?inverter_q ?phase_mrid ?phase_name ?phase_p ?phase_q ?inverter_mode ?inverter_max_q ?inverter_min_q
    ORDER BY ?inverter_mrid
        """ % self.model_mrid
        results = self.gapps.query_data(query, timeout=60)
        results_obj = results['data']
        Inv = []
        inverter = results_obj['results']['bindings']
        for i in inverter:
            name = i['inverter_name']['value']
            message = dict(name = i['inverter_name']['value'],
                        mrid  = i['inverter_mrid']['value'],
                        measid = [],
                        ratedS = 0.001 * float(i['inverter_rated_s']['value']),
                        ratedP = 0.001 * float(i['inverter_p']['value']))
            Inv.append(message)   
        

        query = """
    PREFIX r: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c: <http://iec.ch/TC57/CIM100#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT ?inverter_mrid ?meas_mrid ?phase
    WHERE {
    # Update for your feeder, or remove for all feeders.
    VALUES ?feeder_mrid {"%s"}
    ?s r:type ?type.
    ?s c:IdentifiedObject.mRID ?meas_mrid.
    ?s c:Measurement.PowerSystemResource ?eq.
    ?s c:Measurement.Terminal ?trm.
    ?s c:Measurement.phases ?phsraw.
    {bind(strafter(str(?phsraw),"PhaseCode.") as ?phase)} .
    ?eq c:IdentifiedObject.mRID ?inverter_mrid.
    ?eq r:type c:PowerElectronicsConnection.
    ?eq c:Equipment.EquipmentContainer ?fdr.
    ?fdr c:IdentifiedObject.mRID ?feeder_mrid.
    }
    ORDER BY ?inverter_mrid
        """ % self.model_mrid
        results = self.gapps.query_data(query, timeout=60)
        results_obj = results['data']
        inv_meas = results_obj['results']['bindings']        
        for im in inv_meas:
            mrid  = im['inverter_mrid']['value']
            for i in Inv:
                if i['mrid'] == mrid:
                    i['measid'] = im['meas_mrid']['value']

        # print(Inv)
        print('Inverter..')


    def distributed_generators(self):
        query = """
        # SynchronousMachine - DistSyncMachine
    PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c:  <http://iec.ch/TC57/CIM100#>
    SELECT ?name ?bus ?ratedS ?ratedU ?p ?q ?id ?fdrid WHERE {
    VALUES ?fdrid {"%s"}  # 123 bus
    ?s r:type c:SynchronousMachine.
    ?s c:IdentifiedObject.name ?name.
    ?s c:Equipment.EquipmentContainer ?fdr.
    ?fdr c:IdentifiedObject.mRID ?fdrid.
    ?s c:SynchronousMachine.ratedS ?ratedS.
    ?s c:SynchronousMachine.ratedU ?ratedU.
    ?s c:SynchronousMachine.p ?p.
    ?s c:SynchronousMachine.q ?q. 
    ?s c:IdentifiedObject.mRID ?id.
    OPTIONAL {?smp c:SynchronousMachinePhase.SynchronousMachine ?s.
    ?smp c:SynchronousMachinePhase.phase ?phsraw.
    bind(strafter(str(?phsraw),"SinglePhaseKind.") as ?phs) }
    ?t c:Terminal.ConductingEquipment ?s.
    ?t c:Terminal.ConnectivityNode ?cn. 
    ?cn c:IdentifiedObject.name ?bus
    }
    GROUP by ?name ?bus ?ratedS ?ratedU ?p ?q ?id ?fdrid
    ORDER by ?name
        """ % self.model_mrid
        results = self.gapps.query_data(query, timeout=60)
        results_obj = results['data']
        DERs = []
        MT = results_obj['results']['bindings']
        for d in MT:
            message = dict(name = d['name']['value'],
                           mrid  = d['id']['value'],
                           bus = d['bus']['value'],
                           ratedS = 0.001 * float(d['ratedS']['value']))
            DERs.append(message)  

    
        query = """
       PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c:  <http://iec.ch/TC57/CIM100#>
    SELECT ?name ?bus ?ratedS ?ratedU ?ipu ?ratedE ?storedE ?state ?p ?q ?id ?fdrid WHERE {
    ?s r:type c:BatteryUnit.
    ?s c:IdentifiedObject.name ?name.
    ?pec c:PowerElectronicsConnection.PowerElectronicsUnit ?s.
    VALUES ?fdrid {"%s"}
    ?pec c:Equipment.EquipmentContainer ?fdr.
    ?fdr c:IdentifiedObject.mRID ?fdrid.
    ?pec c:PowerElectronicsConnection.ratedS ?ratedS.
    ?pec c:PowerElectronicsConnection.ratedU ?ratedU.
    ?pec c:PowerElectronicsConnection.maxIFault ?ipu.
    ?s c:BatteryUnit.ratedE ?ratedE.
    ?s c:BatteryUnit.storedE ?storedE.
    ?s c:BatteryUnit.batteryState ?stateraw.
    bind(strafter(str(?stateraw),"BatteryState.") as ?state)
    ?pec c:PowerElectronicsConnection.p ?p.
    ?pec c:PowerElectronicsConnection.q ?q. 
    OPTIONAL {?pecp c:PowerElectronicsConnectionPhase.PowerElectronicsConnection ?pec.
    ?pecp c:PowerElectronicsConnectionPhase.phase ?phsraw.
    bind(strafter(str(?phsraw),"SinglePhaseKind.") as ?phs) }
    ?s c:IdentifiedObject.mRID ?id.
    ?t c:Terminal.ConductingEquipment ?pec.
    ?t c:Terminal.ConnectivityNode ?cn. 
    ?cn c:IdentifiedObject.name ?bus
    }
    GROUP by ?name ?bus ?ratedS ?ratedU ?ipu ?ratedE ?storedE ?state ?p ?q ?id ?fdrid
    ORDER by ?name
        """ % self.model_mrid
        results = self.gapps.query_data(query, timeout=60)
        results_obj = results['data']
        ESS = results_obj['results']['bindings']
        for d in ESS:
            message = dict(name = d['name']['value'],
                           mrid  = d['id']['value'],
                           bus = d['bus']['value'],
                           ratedS = 0.001 * float(d['ratedS']['value']))
            DERs.append(message)  

        return DERs
        
    def linepar(self, Linepar):

        # Checking Linepar and forming R and X matrix to be 9 by 9 always. Especially the capacitor control element
        # and two phase line. Other will be always 9*9
        for line in Linepar:
            if line['nPhase'] == 2:
                line['r'] = [1.13148, 0.0, 0.142066, 0.0, 0.001, 0.0, 0.142066, 0.0, 1.13362]
                line['x'] = [0.884886, 0.0, 0.366115, 0.0, 0.001, 0.0, 0.366115, 0.0, 0.882239]

        for line in Linepar:
            if line['nPhase'] == 1 and line['Phase'] == 'A':
                r = line['r']
                x = line['x']
                line['r'] = [r[0], 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001]
                line['x'] = [x[0], 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001]

        for line in Linepar:
            if line['nPhase'] == 1 and line['Phase'] == 'B':
                r = line['r']
                x = line['x']
                line['r'] = [0.001, 0.0, 0.0, 0.0, r[0], 0.0, 0.0, 0.0, 0.001]
                line['x'] = [0.001, 0.0, 0.0, 0.0, x[0], 0.0, 0.0, 0.0, 0.001]

        for line in Linepar:
            if line['nPhase'] == 1 and line['Phase'] == 'C':
                r = line['r']
                x = line['x']
                line['r'] = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, r[0]]
                line['x'] = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, x[0]]

        cap = [32, 605, 482, 1811]
        for line in Linepar:
            if line['index'] in cap:
                line['r'] = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001]
                line['x'] = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001]
        
        # Add few more lines for DG virtual switch
        message = dict(line = 'dgv1',
                            index = 2754,
                            from_br = 'SOURCEBUS',
                            to_br = 'M1209DER480-1',
                            is_Switch = 1,
                            length = 0.001,
                            nPhase = 3,
                            Phase = 'ABC',
                            r = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001],
                            x = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001])
        Linepar.append(message)
        message = dict(line = 'dgv2',
                            index = 2755,
                            from_br = 'SOURCEBUS',
                            to_br = 'M1142DER480-1',
                            is_Switch = 1,
                            length = 0.001,
                            nPhase = 3,
                            Phase = 'ABC',
                            r = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001],
                            x = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001])
        Linepar.append(message)

        message = dict(line = 'dgv3',
                            index = 2756,
                            from_br = 'SOURCEBUS',
                            to_br = 'M2001DER-1',
                            is_Switch = 1,
                            length = 0.001,
                            nPhase = 3,
                            Phase = 'ABC',
                            r = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001],
                            x = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001])
        Linepar.append(message)

        message = dict(line = 'dgv4',
                            index = 2757,
                            from_br = 'SOURCEBUS',
                            to_br = 'M1069DER480-1',
                            is_Switch = 1,
                            length = 0.001,
                            nPhase = 3,
                            Phase = 'ABC',
                            r = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001],
                            x = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001])
        Linepar.append(message)

        message = dict(line = 'dgv5',
                            index = 2758,
                            from_br = 'SOURCEBUS',
                            to_br = 'M1089DER480-1',
                            is_Switch = 1,
                            length = 0.001,
                            nPhase = 3,
                            Phase = 'ABC',
                            r = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001],
                            x = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001])
        Linepar.append(message)

        message = dict(line = 'dgv6',
                            index = 2759,
                            from_br = 'SOURCEBUS',
                            to_br = 'M1089DER480-2',
                            is_Switch = 1,
                            length = 0.001,
                            nPhase = 3,
                            Phase = 'ABC',
                            r = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001],
                            x = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001])
        Linepar.append(message)

        message = dict(line = 'dgv7',
                            index = 2760,
                            from_br = 'SOURCEBUS',
                            to_br = 'M1026CHP-1',
                            is_Switch = 1,
                            length = 0.001,
                            nPhase = 3,
                            Phase = 'ABC',
                            r = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001],
                            x = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001])
        Linepar.append(message)

        return Linepar