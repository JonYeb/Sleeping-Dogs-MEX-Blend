import bpy,os
import Blender,struct
from Blender import *
from struct import *
import zlib
from Blender.Mathutils import *
from myFunction import *

#Blender 249 python experimental script for importing models from Sleeping Dogs PC game
#install python 2.6
#unpack 'CharactersHD.big' from game with SDBIGUnpacker.exe (www.xentax.com,www.google)
#run script with alt+p 
#select *.perm.bin file
#it work for autotexturing and weighting
#no bones 
#script is free

def ddsheader():
	ddsheader = '\x44\x44\x53\x20\x7C\x00\x00\x00\x07\x10\x0A\x00\x00\x04\x00\x00\x00\x04\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x0B\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00\x05\x00\x00\x00\x44\x58\x54\x31\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x10\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
	return ddsheader
   

def dds(dxt,compress):
			new=open(model_dir+os.sep+newname+'.dds','wb')
			new.write(ddsheader())
			new.seek(0xC)
			new.write(hh)
			new.seek(0x10)
			new.write(w)
			new.seek(0x54)
			new.write(dxt)
			new.seek(128)
			if compress==1: 
				zdata=zlib.decompress(plik.read(what[m][3]))
			else:
				zdata=plik.read(what[m][3])
			new.write(zdata)
			new.close()
			print plik.tell()

	
def bin_parser(filename):
	
	tempfile=None
	
	g.debug=False#True
	
	streams={}
	materials={}
	streamsID=[]
	mesh_list=[]
	meshID=0
	bonenamelist=[]
	
	while(True):
		if g.tell()==g.fileSize():break
		vm=g.i(4)
		t=g.tell()	
		g.seek(vm[3],1)  
		vc=g.i(7)
		g.word(36)
		if vm[0]==-1742448933:
			vn=g.i(8)
			g.B(160)
			for m in range(vn[1]):
				bonenamelist.append(g.word(64))
			for m in range(vn[1]):
				v1=g.H(1)[0]*2**-14
				v2=g.H(1)[0]*2**-14 
				v3=g.H(1)[0]*2**-14 
				v4=g.H(1)[0]*2**-14 
				print v1,v2,v3,v4 
		
		if vm[0]==-843079536:#texture
			tempfile=open(filename.replace('.perm.','.temp.'),'rb')
			temp=BinaryReader(tempfile)
			vn=g.i(55)
			w,h,dxt=None,None,None
			if vn[4]==65546:
				w,h=2048,2048
			if vn[4]==65545:
				w,h=1024,1024
			if vn[4]==65544:
				w,h=512,512
			if vn[4]==65543:
				w,h=256,256
			if vn[4]==65542:
				w,h=128,128
			if vn[4]==65542:
				w,h=64,64
			if vn[1]==1:
				dxt='DXT1'
			if vn[1]==3:
				dxt='DXT5'
			if vn[1]==2:
				dxt='DXT3'
			
			if w!=None:
				new=open(dirname+os.sep+str(vc[3])+'.dds','wb')
				new.write(ddsheader())
				new.seek(0xC)
				new.write(struct.pack('i',w))
				new.seek(0x10)
				new.write(struct.pack('i',h))
				new.seek(0x54)
				new.write(dxt)
				new.seek(128)
				
				tempfile.seek(vn[12])
				new.write(tempfile.read(vn[13]))
				new.close()
			tempfile.close()
		
		
		if vm[0]==1845060531:#meshes info section
			
			g.tell()
			vn=g.i(15)
			vn=g.i(17)
			off=g.tell()
			offsetlist=g.i(vn[1])
			for m in range(vn[1]):
				g.seek(m*4+off+offsetlist[m])
				va=g.i(36)
				if str(va[11]) in streams:
					materialID=va[3]
					material=Facesgroups()
					material.name=str(model_id)+'-mat-'+str(m)
					try:material.diffuse=dirname+os.sep+str(materials[str(materialID)]['diffID'])+'.dds'
					except:pass
					if va[15] not in streamsID:
						streamsID.append(va[15])
						mesh=Mesh() 
						mesh.name=str(model_id)+'-model-'+str(meshID)
						#mesh.BINDSKELETON=True
						mesh.TRIANGLE=True
						mesh_list.append(mesh)
						meshID+=1
					mesh=mesh_list[streamsID.index(va[15])]
					
					#go to indices stream
					print va[11]
					indicesstream=streams[str(va[11])]
					g.seek(indicesstream[1])			
					mesh.indiceslist.extend(g.h(indicesstream[0][4])[va[29]:va[29]+va[30]*3])
					print len(mesh.indiceslist)/3-va[30],va[30],indicesstream[1]
					material.faceIDstart=len(mesh.indiceslist)/3-va[30]
					material.faceIDcount=va[30]
					mesh.facesgroupslist.append(material)
					
					#go to uv stream
					if str(va[23]) in streams:
						uvstream=streams[str(va[23])]
						g.seek(uvstream[1])
						for n in range(uvstream[0][4]):
							tn=g.tell()
							mesh.vertexuvlist.append(g.half(2))
							g.seek(tn+uvstream[0][3])
					
					#go to skin stream
					if str(va[19]) in streams:
						vertexgroups=Vertexgroups()
						skinstream=streams[str(va[19])]
						print 'skin',skinstream
						g.seek(skinstream[1])
						vertexgroups.vertexIDstart=len(mesh.vertexlist)
						vertexgroups.vertexIDcount=skinstream[0][4]	
						for n in range(skinstream[0][4]):
							tn=g.tell()
							vertexgroups.indiceslist.append(g.B(4))
							w1=g.B(1)[0]/255.0
							w2=g.B(1)[0]/255.0
							w3=g.B(1)[0]/255.0
							w4=g.B(1)[0]/255.0
							vertexgroups.weightslist.append([w1,w2,w3,w4])
							g.seek(tn+skinstream[0][3])
						vertexgroups.usedbones=bonenamelist	
						mesh.vertexgroupslist.append(vertexgroups)	
						
					#go to vertex position stream
					print 'vertexstream',va[15]
					vertexstream=streams[str(va[15])]
					g.seek(vertexstream[1])
					g.debug=False
					if vertexstream[0][3]==16:
						for n in range(vertexstream[0][4]):
							tn=g.tell()
							x=g.h(1)[0]*2**-14
							y=g.h(1)[0]*2**-14
							z=g.h(1)[0]*2**-14
							mesh.vertexlist.append([x,y,z])
							g.seek(tn+vertexstream[0][3])
					if vertexstream[0][3]==12:
						for n in range(vertexstream[0][4]):
							tn=g.tell()
							mesh.vertexlist.append(g.f(3))
							g.seek(tn+vertexstream[0][3])
					
				#g.debug=True
				#break
				
		
		if vm[0]==-168275601:#material section
			#g.debug=False	
			materials[str(vc[3])]={}		
			g.tell()
			vn=g.i(8)
			for m in range(vn[4]):
				vp=g.i(8)
				if vp[0]==-589273463:
					materials[str(vc[3])]['diffID']=vp[6]
				if vp[0]==-1396934011:
					materials[str(vc[3])]['specID']=vp[6]
			g.i(4)  
			#g.debug=True
			
		if vm[0]==2056721529:#streams section:vertex position,vertex uv,vertex indices,vertex skin
			v=g.i(32)
			streams[str(vc[3])]=[v,g.tell()]
		g.seek(t+vm[1])	
	g.tell()
		
	for mesh in mesh_list:
		mesh.draw()
	
			
def file_format_parser(filename):
	print
	print filename
	print
	global g,model_id,txt,text,dirname
	global skeleton,used_bones
	skeleton=None
	used_bones=None
	
			
	
	model_id=create_object_name()
	dirname=sys.dirname(filename)
	ext=filename.split('.')[-1].lower()
	
	if ext=='bin':
		file=open(filename,'rb')
		g=BinaryReader(file)
		#g.logfile=open(filename+'.log','w')
		#g.log=True
		bin_parser(filename)
		file.close()
		#g.logfile.close()
	
Window.FileSelector(file_format_parser) 