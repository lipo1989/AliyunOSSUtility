import httplib
import os

# specify the bucket info
upload_bucket = 'junyivideo2'
upload_endpoint = 'oss-cn-hangzhou.aliyuncs.com'
bucket_url = upload_bucket+'.'+upload_endpoint

id_list = []
filename = os.path.dirname(os.path.abspath(__file__))+'/youtube_id_junyi.csv'
with open(filename, 'rU') as f:
	id_list = f.read().splitlines()

missing_list = []
for youtube_id in id_list:
	object_name = '/'+youtube_id+'.mp4'
	conn = httplib.HTTPConnection(bucket_url)
	conn.request("GET", object_name)
	r1 = conn.getresponse()
	if str(r1.status)+r1.reason != '200OK':
		missing_message = ','.join([youtube_id, str(r1.status), r1.reason])
		print missing_message
		missing_list.append(missing_message)

filename = os.path.dirname(os.path.abspath(__file__))+'/youtube_id_missing.csv'
with open(filename, 'wb') as f:
	f.write('\n'.join(missing_list))

print 'Finished. Please check youtube_id_missing.csv'
