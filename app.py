from flask import Flask
from flask_restful import Resource, Api
from resources.compute import Compute, ComputeReport
# from resources.ceph import Ceph


app = Flask(__name__)
app.secret_key = 'long'
api = Api(app)

api.add_resource(Compute, '/compute')
api.add_resource(ComputeReport, '/compute/report')
#api.add_resource(Storage, '/storage')
#api.add_resource(StorageReport, '/storage/report')

# api.add_resource(Storage, '/storage')

if __name__ == '__main__':
    app.run(port=5000, debug=True)
