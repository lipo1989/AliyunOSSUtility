import os, threading
from oss.oss_api import OssAPI
from xml.etree import ElementTree


class UploadThread(threading.Thread):

    def __init__(self, oss, filename, pos_list, len_list, part_id_list, md5_list, index):
        threading.Thread.__init__(self)
        self.oss = oss
        self.filename = filename
        self.pos_list = pos_list
        self.len_list = len_list
        self.part_id_list = part_id_list
        self.md5_list = md5_list
        self.index = index

    def run(self):
    	with open(self.filename, 'rb') as f:
    		f.seek(self.pos_list[self.index])
    		data = f.read(self.len_list[self.index])
    	tmp_file = self.filename+str(self.part_id_list[self.index]) 
    	with open(tmp_file, 'wb') as f:
    		f.write(data)
        self.md5_list[self.index] = self.oss.upload_part(upload_bucket, object_name, tmp_file, upload_id, self.part_id_list[self.index]).getheader('ETag')
        os.remove(tmp_file)


# Please specify the bucket to upload files into
upload_bucket = 'junyivideo2'
upload_endpoint = 'oss.aliyuncs.com'
access_id = 'tA1aeojf8SZ17iRn'
access_key = 'wojd90btN64jCK5Dkab0mH0Fkhl16u'
patch_size = 1024 * 1024 * 5


filedir = os.path.dirname(os.path.abspath(__file__)) + '/upload_files/'
list_file = os.path.dirname(os.path.abspath(__file__)) + '/upload_list.txt'

while True:
    with open(list_file, 'rU') as f:
    	list_data = f.read()
    	upload_list = list_data.splitlines()

    if list_data == '':
    	break

    object_name = upload_list[0]
    total = len(upload_list)
    with open(list_file, 'wb') as f:
	    f.write('/n'.join(upload_list[1:]))

    print str(total), 'files to upload...'
    try:
        filename = filedir + object_name

        oss = OssAPI(upload_endpoint, access_id, access_key)
        upload_id = ElementTree.fromstring(oss.init_multi_upload(upload_bucket, object_name).read()).find('UploadId').text

        file_size = os.path.getsize(filename)
        pos_list = range(0, file_size, patch_size)
        len_list = [patch_size] * int(file_size/patch_size) + [file_size%patch_size]
        part_id_list = range(1, len(pos_list)+1)
        md5_list = range(len(pos_list))

        thread_pool = []
        for index, part_id in enumerate(part_id_list):
	        upload_thread = UploadThread(oss,
		        filename,
    		    pos_list,
	    	    len_list,
		        part_id_list,
		        md5_list,
		        index
	        )
	        thread_pool.append(upload_thread)
	        upload_thread.start()

        for upload_thread in thread_pool:
	        upload_thread.join()

        xml_message = ElementTree.Element('CompleteMultipartUpload')
        for i in range(len(part_id_list)):
            xml_message_part = ElementTree.SubElement(xml_message, 'Part')
            xml_message_part_number = ElementTree.SubElement(xml_message_part, 'PartNumber')
            xml_message_part_number.text = str(part_id_list[i])
            xml_message_part_etag = ElementTree.SubElement(xml_message_part, 'ETag')
            xml_message_part_etag.text = str(md5_list[i])
        xml_message = ElementTree.tostring(xml_message)

        upload_res = oss.complete_upload(upload_bucket, object_name, upload_id, xml_message).read()
        upload_res_root = ElementTree.fromstring(upload_res)

        if upload_res_root.tag == 'CompleteMultipartUploadResult':
        	print object_name, 'uploaded;', str(total-1), 'files remain'
        	logfile = os.path.dirname(os.path.abspath(__file__)) + '/log.txt'
        	with open(logfile, 'w+') as f:
        		f.write(upload_res+'\n')
        else:
            print object_name, 'upload failed, please check log'
            errorfile = os.path.dirname(os.path.abspath(__file__)) + '/erro_list.txt'
            with open(errorfile, 'w+') as f:
        	    f.write(object_name+'\n')
        	    f.write(upload_res+'\n')
    	    skipfile = os.path.dirname(os.path.abspath(__file__)) + '/skip_list.txt'
            with open(skipfile, 'w+') as f:
    	        f.write(object_name+'\n')

    except Exception as e:
        print object_name, 'upload failed with error message %s' % e
        errorfile = os.path.dirname(os.path.abspath(__file__)) + '/erro_list.txt'
        with open(errorfile, 'w+') as f:
            f.write(object_name+'\n')
            f.write(e+'\n')
        skipfile = os.path.dirname(os.path.abspath(__file__)) + '/skip_list.txt'
        with open(skipfile, 'w+') as f:
            f.write(object_name+'\n')
