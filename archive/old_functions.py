"""
    def getdatasets_filtered(self, key, archive, stream):
        if key[-1] != '/':
            key += '/'
        out = []
        for name in archive[key]:
            if any(key[1:-1] in s for s in self.checked_list[stream]):
                #print('KEY', key[1:-1])
                path = key + name
                if isinstance(archive[path], h5py.Dataset):
                    out += [path]
                else:
                    out += self.getdatasets_filtered(path, archive)
        return out

    def clusters_check(self):
        self.clusters = {}
        self.clusters['Select all'], self.clusters['BPM'], self.clusters['BAM'], self.clusters['BCM'], self.clusters['XGM'], self.clusters['TOROID'], self.clusters[
            'DAQ_INFO'], self.clusters['XGM_PROPERTIES'], self.clusters['SA1'], self.clusters['SA2'], self.clusters['SA3'], self.clusters['RF'], \
            self.clusters['TIMINGINFO'],  self.clusters['MAGNET'], self.clusters['HOLDDMA'], self.clusters['CHICANE'], self.clusters['UNDULATOR'], \
            self.clusters['BEAM_ENERGY_MEASUREMENT'],  self.clusters['CHARGE'], self.clusters['HOLDSCOPE'], self.clusters['BHM'], self.clusters['KICKER'], \
            self.clusters['FARADAY'],  self.clusters['DCM'], self.clusters['BLM'] \
            = [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []
        self.clusters['Select all'] = self.channel_list
        for channel in self.channel_list:
            if channel.find('BPM') != -1:
                self.clusters['BPM'].append(channel)
            if channel.find('BAM.DAQ') != -1:
                self.clusters['BAM'].append(channel)
            if channel.find('BCM/BCM') != -1:
                self.clusters['BCM'].append(channel)
            if channel.find('XGM/XGM') != -1:
                self.clusters['XGM'].append(channel)
            if channel.find('TOROID') != -1:
                self.clusters['TOROID'].append(channel)
            if channel.find('DISTRIBUTOR') != -1:
                self.clusters['DAQ_INFO'].append(channel)
            if channel.find('XGM.POSMON') != -1 or channel.find('XGM.CURRENT') != -1 or channel.find('XGM.TEMP') != -1 or channel.find('XGM.PHOTONFLUX') != -1 or channel.find('XGM.GAS') != -1 or channel.find('XGM.PRESSURE') != -1:
                self.clusters['XGM_PROPERTIES'].append(channel)
            if channel.find('SA1') != -1:
                self.clusters['SA1'].append(channel)
            if channel.find('SA2') != -1:
                self.clusters['SA2'].append(channel)
            if channel.find('SA3') != -1:
                self.clusters['SA3'].append(channel)
            if channel.find('TIMINGINFO') != -1:
                self.clusters['TIMINGINFO'].append(channel)
            if channel.find('MAGNETS/MAGNET') != -1:
                self.clusters['MAGNET'].append(channel)
            if channel.find('HOLDDMA') != -1:
                self.clusters['HOLDDMA'].append(channel)
            if channel.find('CHICANE') != -1:
                self.clusters['CHICANE'].append(channel)
            if channel.find('UNDULATOR') != -1:
                self.clusters['UNDULATOR'].append(channel)
            if channel.find('RF/MODULATOR') != -1:
                self.clusters['RF'].append(channel)
            if channel.find('BEAM_ENERGY_MEASUREMENT') != -1:
                self.clusters['BEAM_ENERGY_MEASUREMENT'].append(channel)
            if channel.find('CHARGE.ML') != -1:
                self.clusters['CHARGE'].append(channel)
            if channel.find('HOLDSCOPE') != -1:
                self.clusters['HOLDSCOPE'].append(channel)
            if channel.find('BHM/BHM') != -1:
                self.clusters['BHM'].append(channel)
            if channel.find('KICKER.ADC') != -1:
                self.clusters['KICKER'].append(channel)
            if channel.find('FARADAY') != -1:
                self.clusters['FARADAY'].append(channel)
            if channel.find('DCM/DCM') != -1:
                self.clusters['DCM'].append(channel)
            if channel.find('BLM/BLM') != -1:
                self.clusters['BLM'].append(channel)
        self.fill_filter_table()

    def clustering(self):
        # max number of strings per cluster
        MAX_NB_STRINGS_PER_CLUSTER = 50
        # result dict
        self.clusters = {}
        # add strings to trie
        print(self.channel_list)
        root = trie.TrieNode('', None)
        for string in self.channel_list:
            trie.add(root, string)

        # get clusters from trie
        clusters_nodes = []
        trie.chunk_into_clusters(
            root, MAX_NB_STRINGS_PER_CLUSTER, clusters_nodes)

        # get strings associated with each clusters nodes
        for cluster_node in clusters_nodes:
            cluster_node_string = trie.retrieve_string(cluster_node)

            self.clusters[cluster_node_string] = []

            # get strings contained in each cluster
            end_nodes = []
            trie.find_end_nodes(cluster_node, end_nodes)

            if cluster_node.is_string_finished:
                self.clusters[cluster_node_string].append(cluster_node_string)

            for end_node in end_nodes:
                end_node_string = trie.retrieve_string(end_node)
                self.clusters[cluster_node_string].append(end_node_string)

        # print results
        for cluster_name, cluster_strings in self.clusters.items():
            print("\n{}:".format(cluster_name))
            for string in cluster_strings:
                print("\t{}".format(string))

matches = []
file_date_list = []
matches = [re.search(
    r'\d{4}\d{2}\d{2}T\d{2}\d{2}\d{2}', i) for i in self.file_list]
for match in matches:
    date = datetime.strptime(match.group(), '%Y%m%dT%H%M%S').date()
    file_date_list.append(date)
print(file_date_list)

    def write_hdf5_files(self):
        with self.fd as new_data:
            file_count = 1
            for inputfile in self.files_match['filename']:
                data = h5py.File(self.storagepath + '/'+inputfile, 'r')
                # read as much datasets as possible from the old HDF5-file
                datasets = self.getdatasets_filtered('/', data)
                # get the group-names from the lists of datasets
                groups = list(set([i[::-1].split('/', 1)[1][::-1]
                                   for i in datasets]))
                groups = [i for i in groups if len(i) > 0]

                # sort groups based on depth
                idx = np.argsort(np.array([len(i.split('/')) for i in groups]))
                groups = [groups[i] for i in idx]

                # create all groups that contain dataset that will be copied
                for group in groups:
                    if not group in new_data.keys():
                        new_data.create_group(group)
                    else:
                        print(group, " is already in the file")

                # copy datasets
                for path in datasets:
                    # - get group name
                    group = path[::-1].split('/', 1)[1][::-1]
                    # - minimum group name
                    if len(group) == 0:
                        group = '/'
                        # - copy data
                    print(path)
                    data.copy(path, new_data[group])

            sz = os.path.getsize(self.outpath + '/'+self.hd5file)
            sz_MB = sz/1048576
            if sz_MB > (self.ui.thresholdSpinBox.value()*1000):
                file_count += 1
                ext_inc = str(file_count)
                self.create_hdf5_file(ext_inc)

    def create_hdf5_file(self, ext):
        now = datetime.now()
        timestamp = now.strftime('%Y-%m-%dT%H:%M:%S') + \
            ('-%02d' % (now.microsecond / 10000))

        self.hd5file = 'xfel_' + self.start_timestamp_str + \
            '_' + self.stop_timestamp_str + '_' + ext + '.hdf5'
        print('writing into %s . . . ' % (self.hd5file), end='', flush=True)
        self.fd = h5py.File(self.outpath
                            + '/' + self.hd5file, "w")
        # point to the default data to be plotted
        self.fd.attrs[u'default'] = u'entry'
        # give the HDF5 root some more attributes
        self.fd.attrs[u'file_name'] = self.hd5file
        self.fd.attrs[u'file_time'] = timestamp
        self.fd.attrs[u'creator'] = os.path.basename(sys.argv[0])
        self.fd.attrs[u'HDF5_Version'] = h5py.version.hdf5_version
        self.fd.attrs[u'h5py_version'] = h5py.version.version
"""
