#@ File (label="Input directory 1", style="directory") inputdirec1
#@ File (label="Input directory 2", style="directory") inputdirec2


#Run this script in the IMJ script window, File->Open-> imjscript.py
#Set direcotories to the 2 directories with the batches of data in them, here that is rab7 rilp.
#You can do this via the brows utility youll get when you open this script.
#Once you do this and run, a new folder calld "ouput" will appear in the "Data" folder.
# This output folder will contain the composite of binarized images, with contrast you set.
#The numbers on each "merged" image correspond to numbers on the files in rab7 and rilp.

import os
import shutil
import sys

from ij.process import ImageProcessor
from ij import IJ,ImageStack, ImagePlus  
from ij.io import FileSaver
from ij.plugin import Duplicator
from os import path


def get_image_paths(path):
	image_files = os.listdir(path)
	return [path + '/' + image_file for image_file in image_files if 'tif' in image_file]


def save_copy(path, base_dir):  
	copy_dir = base_dir+'copy/'
	name = os.path.basename(path)

	copy_name = name[:-4]+'copy'
	copy_path = copy_dir+ copy_name

	img = IJ.openImage(path)
	copy = Duplicator().run(img)
	IJ.saveAs(copy,"tiff",copy_path)


def copy_dir(base_dir):
	images_paths = get_image_paths(base_dir)
	copy_dir = base_dir+ 'copy/'
	try:
		os.mkdir(copy_dir)
	except:
		copy_dir=copy_dir[:-1] + '1/'
		os.mkdir(copy_dir)

	for img_path in images_paths:
		save_copy(img_path,base_dir)


def set_contrast(direc, saturation= .5):
	images_paths = get_image_paths(direc)
	for img_path in images_paths:
		img = IJ.openImage(img_path)
		IJ.run(img,"Enhance Contrast...", "saturated="+str(saturation))
		IJ.saveAs(img, "tiff", img_path)


def binarize(direc):
	images_paths = get_image_paths(direc)
	for img_path in images_paths:
		img = IJ.openImage(img_path)
		IJ.run(img, "Make Binary","")
		IJ.saveAs(img, "tiff", img_path)


def pre_process_imgs(direc, saturation = .5):
	set_contrast(direc,saturation)
	binarize(direc)


def get_alt_pixel(pixel_1, pixel_2, variant = True):
        if pixel_1 and pixel_2:
                return 0
        if (not pixel_1) and (not pixel_2):
                return 0
        if variant:
        	if (not pixel_1) and (pixel_2):
        		return 255
        	return 0
        else: 
        	if (not pixel_2) and pixel_1:
        		return 255
       	return 0
        

def merge(path1, path2, thresh1, thresh2, granular = False):

	img1 = IJ.openImage(path1)
	img2 = IJ.openImage(path2)

	width1,height1 = img1.getWidth(), img1.getHeight()
	width2,height2 = img2.getWidth(), img2.getHeight()

	output = IJ.createImage("T_image", "16-bit", width1, height1, 1)
	output = output.getProcessor()

	alt_output_1 = IJ.createImage("T_image", "16-bit", width1, height1, 1)
	alt_output_1 = alt_output_1.getProcessor()

	alt_output_2 = IJ.createImage("T_image", "16-bit", width1, height1, 1)
	alt_output_2 = alt_output_2.getProcessor()

	img1_output = IJ.createImage("T_image", "16-bit", width1, height1, 1)
	img1_output = img1_output.getProcessor()

	img2_output = IJ.createImage("T_image", "16-bit", width2, height2, 1)
	img2_output = img2_output.getProcessor()             
           
	composite_pixels = []
	img1_info = img1.getProcessor().convertToFloat()
	img2_info = img2.getProcessor().convertToFloat()

	if granular:
		thresh1 = IJ.getNumber('Threshold1', float(thresh1))
		thresh2 = IJ.getNumber('Threshold2', float(thresh2))
		
	thresh_val1 = max(img1_info.getPixels())*(thresh1/100)
	thresh_val2 = max(img2_info.getPixels())*(thresh2/100)

	for row in range(height1):
		for column in range(width1):            
			img1_pixel = img1_info.getPixelValue(column, row, )
			if img1_pixel < thresh_val1:
				img1_pixel = 0
			else:
				img1_pixel = 255

			img2_pixel = img2_info.getPixelValue(column,row,)
			if img2_pixel < thresh_val2:
				img2_pixel = 0
			else:
				img2_pixel = 255

			min_pixel = int(min(img1_pixel, img2_pixel))
			alt_pixel_1 = get_alt_pixel(img1_pixel, img2_pixel)
			alt_pixel_2 = get_alt_pixel(img1_pixel, img2_pixel, variant = False)

			output.putPixel(column, row, min_pixel)
			alt_output_1.putPixel(column, row, alt_pixel_1)
			alt_output_2.putPixel(column, row, alt_pixel_2)

			img1_output.putPixel(column, row, img1_pixel)
			img2_output.putPixel(column, row, img2_pixel)

	output = ImagePlus("my_image", output.convertToFloat())
	alt_output_1 = ImagePlus("my_image", alt_output_1.convertToFloat())
	alt_output_2 = ImagePlus("my_image", alt_output_2.convertToFloat())
	
	img1_output = ImagePlus("my_image", img1_output.convertToFloat())
	img2_output = ImagePlus("my_image", img2_output.convertToFloat())   

	if not granular:
		return (output, alt_output_1, alt_output_2, img1_output, img2_output)
		
  	dup = img1_output.duplicate()
  	dup.show()
  	img1.show()
  	satisfied1 = check_satisied()

  	dup.close()
  	img1.close()
  	
  		
  	dup = img2_output.duplicate()
  	dup.show()
  	img2.show()
  	satisfied2 = check_satisied()

  	dup.close()
  	img2.close()
  	
  	if satisfied1 and satisfied2:
		return (output, alt_output_1, alt_output_2, img1_output, img2_output)
	else:
		if not satisfied1:
			thresh1 = 0
		if not satisfied2:
			thresh2 = 0
		return merge(path1, path2, thresh1, thresh2, granular = True)




def sep_merge(path1, path2, thresh1, thresh2, granular = False):

	img1 = IJ.openImage(path1)
	width1,height1 = img1.getWidth(), img1.getHeight()
	img1_output = IJ.createImage("T_image", "16-bit", width1, height1, 1)
	img1_output = img1_output.getProcessor()
	img1_info = img1.getProcessor().convertToFloat()
	satisfied_1 = False

	
	img2 = IJ.openImage(path1)
	width2,height2 = img1.getWidth(), img1.getHeight()
	img2_output = IJ.createImage("T_image", "16-bit", width2, height2, 1)
	img2_output = img2_output.getProcessor()
	img2_info = img2.getProcessor().convertToFloat()
	satisfied_2 = False

	output = IJ.createImage("T_image", "16-bit", width1, height1, 1)
	output = output.getProcessor()

	alt_output_1 = IJ.createImage("T_image", "16-bit", width1, height1, 1)
	alt_output_1 = alt_output_1.getProcessor()

	alt_output_2 = IJ.createImage("T_image", "16-bit", width1, height1, 1)
	alt_output_2 = alt_output_2.getProcessor()

           
	composite_pixels = []
        
	while not satisfied_1:
			img1.show()
			thresh1 = IJ.getNumber('Threshold1', float(thresh1))
			thresh_val1 = max(img1_info.getPixels())*(thresh1/100)
			for row in range(height1):
				for column in range(width1):
					img1_pixel = img1_info.getPixelValue(column, row, )
					if img1_pixel < thresh_val1:
						img1_pixel = 0
					else:
						img1_pixel = 255
					img1_output.putPixel(column, row, img1_pixel)
			img1_out = ImagePlus("my_image", img1_output.convertToFloat())
			dup = img1_out.duplicate()
			dup.show()
			satisfied_1 = check_satisied()

			dup.close()
	img1.close()
                                
                           
	while not satisfied_2:    
			img2.show() 
			thresh2 = IJ.getNumber('Threshold2', float(thresh2))
			thresh_val2 = max(img2_info.getPixels())*(thresh2/100)
			for row in range(height1):
				for column in range(width1):            
					img2_pixel = img2_info.getPixelValue(column, row, )
					if img2_pixel < thresh_val2:
						img2_pixel = 0
					else:
						img2_pixel = 255
					img2_output.putPixel(column, row, img2_pixel)
			img2_out = ImagePlus("my_image", img2_output.convertToFloat())
			dup = img2_out.duplicate()
			dup.show()
			satisfied_2 = check_satisied()

			dup.close()
	img2.close()
                

	for row in range(height1):
		for column in range(width1):            
			img1_pixel = img1_info.getPixelValue(column, row, )
			if img1_pixel < thresh_val1:
				img1_pixel = 0
			else:
				img1_pixel = 255

			img2_pixel = img2_info.getPixelValue(column,row,)
			if img2_pixel < thresh_val2:
				img2_pixel = 0
			else:
				img2_pixel = 255

			min_pixel = int(min(img1_pixel, img2_pixel))
			alt_pixel_1 = get_alt_pixel(img1_pixel, img2_pixel)
			alt_pixel_2 = get_alt_pixel(img1_pixel, img2_pixel, variant = False)

			output.putPixel(column, row, min_pixel)
			alt_output_1.putPixel(column, row, alt_pixel_1)
			alt_output_2.putPixel(column, row, alt_pixel_2)


	output = ImagePlus("my_image", output.convertToFloat())
	alt_output_1 = ImagePlus("my_image", alt_output_1.convertToFloat())
	alt_output_2 = ImagePlus("my_image", alt_output_2.convertToFloat())
	
	return (output, alt_output_1, alt_output_2, img1_out, img2_out)
				
				
def parent_path(path):
	rpath = path[::-1]
	last_slash = (rpath.find('/'))
	return path[:-1*last_slash]


def clean_direc(path, final = False):
	files = os.listdir(path)

	if final:
		for file in files:
			if ('copy' in file):
				file_path = path+'/'+file
				shutil.rmtree(file_path)
	else:
		for file in files:
			if ('output' in file) or ('copy' in file):
				file_path = path+'/'+file
				shutil.rmtree(file_path)

				
def extract_name(path):
	if path[-1] == '/':
		path = path[:-1]
	
	path = path.replace('copy', '')
	path = path.replace('.tif', '')
	path = path.replace(' ', '')
	num_slash = path.count('/')
	path = path.replace('/', '',num_slash-1)

	lslash_index = path.index('/')
	name = path[lslash_index+1:]

	return name

def get_name_index(name):
	if '-' in  name[-2:]:
		return name[-1]
	else:
		return name[-2:]

def get_paired_path(name,paths):
	for path in paths:
		if extract_name(path) == name:
			return path

def check_satisied():
	sat_string = IJ.getString("Satisfied with output?", "Yes")
	if sat_string in ['yes', 'YES', 'Yes', 'Y']:
		return True
	if sat_string in ['Quit', 'quit', 'QUIT']:
		sys.exit()
	return False
	

def direc_merge(direc1, direc2, granular = False):
	name_1 = extract_name(direc1)
	name_2 = extract_name(direc2)

	if not granular:
		thresh1 = IJ.getNumber('Threshold1', 0)
		thresh2 = IJ.getNumber('Threshold2', 0)
	else:
		thresh1 = 0
		thresh2 = 0
		
	Gen_name = name_1 + '-' + name_2

	paths1 = get_image_paths(direc1)
	paths2 = get_image_paths(direc2)

	set_contrast(direc1, 10)
	set_contrast(direc2, 10)

	parent = parent_path(direc1[:-1])
	output_path = parent + Gen_name + '_output'

	os.mkdir(output_path)

	for path1 in paths1:
		subname = extract_name(path1)
		os.mkdir(output_path +'/_' + subname +'_')

		path2 = get_paired_path(subname, paths2)
		
		if path2:

			merged, alt_1, alt_2, imp1, imp2 = sep_merge(path1, path2, thresh1, thresh2, granular = granular)

			merged_path = output_path + '/_' + subname + '_/' + Gen_name + '_collocated_'+ subname
			#alt_path_1= output_path + '/_' + subname + '_/' + name_2 + '_not_' + name_1 + '_' + subname
			#alt_path_2= output_path + '/_' + subname + '_/' + name_1 + '_not_' + name_2 + '_' + subname

			input1_path = output_path + '/_' + subname + '_/' + name_1 + '_'+ subname
			input2_path = output_path + '/_' + subname + '_/' + name_2 + '_' + subname

			#IJ.saveAs(alt_1, "tiff", alt_path_1)
			#IJ.saveAs(alt_2, "tiff", alt_path_2)
			IJ.saveAs(merged, "tiff", merged_path)
			IJ.saveAs(imp1, "tiff", input1_path) 
			IJ.saveAs(imp2, "tiff", input2_path)
			
			imp1.close()
			imp2.close()


path1 = str(inputdirec1)
path2 = str(inputdirec2)

parent = parent_path(path1)
clean_direc(parent)

copy_dir(path1)
copy_path1 = path1+'copy/'

copy_dir(path2)
copy_path2 = path2+'copy/'

direc_merge(copy_path1, copy_path2, granular = True)	
clean_direc(parent, final = True)
