#!/usr/bin/env python3

import os
import boto
from flask import Flask, render_template, redirect, request, url_for, make_response
import exifread

#### Strip credential out before push to CF 
ecs_access_key_id = '<Insert your key here>@ecstestdrive.emc.com'  
ecs_secret_key = '<Insert your key here>'

app = Flask(__name__)

@app.route('/')
def main():
    namespace = ecs_access_key_id.split('@')[0]
    
    start_page = """<!DOCTYPE html>
                    <html lang="en">
                    <head>
                    <style>
                        h1 { 
                            display: block;
                            font-size: 2em;
                            margin-top: 0.67em;
                            margin-bottom: 0.67em;
                            margin-left: 0;
                            margin-right: 0;
                            font-weight: bold;
                            text-align: center
                            }
                    </style>
                    </head>"""
    
    mid_page = """<body style="background-color: #fff;"><h1>Photo Album</h1>"""

    for k in bucket.list():
        http_url = 'http://{ns}.{host}/{bucket}/{img}'.format(
            ns=namespace,
            host='public.ecstestdrive.com',
            bucket=bname,
            img=k.name)

        key = bucket.get_key(k)
        photographer = str(key.get_metadata('photographer'))
        Fstop = key.get_metadata('FNumber')
        shutter = key.get_metadata('ExposureTime')
        FocalLength = key.get_metadata('FocalLengthIn35mmFilm') + "mm"
        camera = key.get_metadata('Make') + " " + key.get_metadata('Model')
        lens = key.get_metadata('LensMake') + " " + key.get_metadata('LensModel')

      #  photo_info = camera + "," + lens + "," + shutter + "," + Fstop + "," + FocalLength

        mid_page += "<p style=\"text-align:center;\"><img src=\"" + http_url + \
                       "\"style=\"width:304px;\"><br>"
        mid_page +="<i>Photographer: " + photographer + "</i><br>"
        mid_page +="<i>Aperture: f/" + Fstop + ", Shutter Speed:" + shutter + ", Camera:" + camera + "</i>"

        mid_page += "</p><hr width=\"50%\">"
        
    end_page = "</body></html>"
    full_page = start_page + mid_page + end_page
    
    return full_page


#### This is the ECS syntax. It requires "host" parameter
session = boto.connect_s3(ecs_access_key_id, ecs_secret_key, host='object.ecstestdrive.com')  

# Get list of photos stored locally
photos = os.listdir("./images")

# Set bucket name
bname = 'images'
path = 'images' #Directory Under which file should get upload

###### Get bucket and display details
bucket = session.get_bucket(bname)

print ("Starting photo uploads ...")

for filename in photos:
    if str(bucket.get_key(filename,
        headers=None, 
        version_id=None, 
        response_headers=None, 
        validate=True)) != 'None':       
        print ('File %s has already been uplodaded. Skipping' % filename)
    else:    
        full_path = path + "/" + filename
        
        name = input("Enter photographer's name for " + filename + ":")

        # Open image file for reading (binary mode)
        f = open(full_path, 'rb')
        
        # Return Exif tags into dictionary
        tags = exifread.process_file(f)
        
        k = bucket.new_key(filename)

        full_key_name = os.path.join(path, filename)
        print ('Uploading %s to ECS bucket %s' % \
               (full_key_name, bucket))

        # Set EXIF metadata on remote object
        for tag in tags.keys():
            if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
                k.set_metadata(str(tag.split()[1]), str(tags[tag]))

        k.set_metadata('photographer', name)
        k.set_contents_from_filename(full_key_name)
        k.set_acl('public-read')

if __name__ == "__main__":
	app.run(debug=False, host='0.0.0.0', \
                port=int(os.getenv('PORT', '5000')), threaded=True)
