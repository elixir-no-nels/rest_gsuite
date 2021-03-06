import json
from collections import OrderedDict
from flask import Flask, request
from gsuite.GSuite import GSuite
from gsuite.GSuiteComposer import composeToString
from gsuite.GSuiteTrack import GSuiteTrack
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

SEP = '->'
ARRAY_SEP = ','
URL_PATH = 'file_url'
TITLE_PATH = 'label_short'
GENOME_PATH = 'assembly_name'
DOC_INFO = 'doc_info'
TRACKS = 'tracks'


@app.route('/')
def index():
    return 'OK'


@app.route('/togsuite', methods=['POST'])
def to_gsuite():
    gsuite = GSuite()
    data = json.loads(request.data, object_pairs_hook=OrderedDict)
    app.logger.debug('Loaded JSON from request: ' + str(len(data)) + ' items')
    for item in data:
        createTracks(gsuite, item)
    app.logger.debug('GSuite with ' + str(gsuite.numTracks()) + ' tracks created.')
    strGsuite = composeToString(gsuite)
    app.logger.debug('GSuite converted to string')

    return strGsuite


def createTracks(gsuite, data):
    if 'tracks' not in data:
        app.logger.debug('No "tracks" element found!')
        app.logger.debug(data)
        return

    trackData = OrderedDict()
    for path, value in dictPaths(data[TRACKS]):
        trackData[path] = value

    dataWithoutTracks = data.copy()
    dataWithoutTracks.pop(TRACKS)
    if DOC_INFO in dataWithoutTracks:
        dataWithoutTracks.pop(DOC_INFO)

    noTrackData = OrderedDict()
    for path, value in dictPaths(dataWithoutTracks):
        noTrackData[path] = value

    # # order the columns as in input json with track attributes first
    resultOrdered = OrderedDict()
    for col in trackData:
        if trackData[col]:
            resultOrdered[col] = trackData[col]

    for col in noTrackData:
        if noTrackData[col]:
            resultOrdered[col] = noTrackData[col]

    uri = resultOrdered.pop(URL_PATH, None)
    if not uri:
        app.logger.debug('Could not find uri in the element!')
        app.logger.debug(resultOrdered)
        return
    gsuite.addTrack(GSuiteTrack(uri=uri, attributes=resultOrdered, title=resultOrdered[TITLE_PATH],
                                genome=resultOrdered[GENOME_PATH]))


def dictPaths(myDict, path=[]):
    for k,v in myDict.iteritems():
        newPath = path + [k]
        if isinstance(v, dict):
            for item in dictPaths(v, newPath):
                yield item
        else:
            # track attributes should not have 'tracks->' in the attribute name
            if newPath[0] == TRACKS:
                yield SEP.join(newPath[1:]), str(v)
            else:
                if isinstance(v, list):
                    yield SEP.join(newPath), ARRAY_SEP.join(v)
                else:
                    yield SEP.join(newPath), str(v)


if __name__ == '__main__':
    app.run(host='0.0.0.0')


