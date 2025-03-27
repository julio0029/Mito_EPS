#!/usr/bin/env python3
#-*- coding: utf-8 -*-
import os
current_path = f"{os.path.dirname(os.path.abspath(__file__))}/"

#FILENAME = f'/Users/jdev864/Library/CloudStorage/OneDrive-TheUniversityofQueensland/Manuscripts/Mito-HTx_2025/Data/Oxygraph_data.csv'
FILENAME = f'/Users/julesdevaux/Library/CloudStorage/OneDrive-TheUniversityofQueensland/Manuscripts/Mito-HTx_2025/Data/Oxygraph_data.csv'
PARAM_COLS = ['Sheep','Group','SubGroup','Storage','Time','Heart']
BETWEENS = ['Group','SubGroup','Storage','Time','Heart']


#////////////////////////////////////// SCRIPT \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
import pandas as pd
import pingouin as pg
from itertools import combinations




def transpose_table(df, param_cols=[]):
	'''
	Transpose a table to have a column for each parameter'''

	cols_to_transpose = [c for c in df.columns if c not in param_cols]
	fdf=[]
	for c in cols_to_transpose:
		tdf=pd.DataFrame(df.loc[:,param_cols+[c]])
		tdf.rename(columns={c:'Value'}, inplace=True)
		tdf['Parameter']=c
		fdf.append(tdf)
	fdf = pd.concat(fdf, axis=0, ignore_index=True)
	return fdf

	

def do_stats(pdf, betweens=[], param_cols=[] , filename=None, _saving=True):
	'''
	Perform ANOVA and Post-hoc tests for each parameter in the pdf
	All saved in an excel file
	'''

	#pdf=pdf.astype('float64', errors='ignore')

	# -------- Pingouin way
	print(f"Performing {len(betweens)}-way ANOVA...")

	# Transpose with extra column for state
	ldf=transpose_table(pdf, param_cols=param_cols)
	
	Stats={}
	for parameter, ppdf in ldf.groupby('Parameter'):
		
		# Rename the 'Value' column to the parameter name
		ppdf.rename(columns={'Value':parameter}, inplace=True)

		# === Do ANOVA ===
		aov=pg.anova(ppdf, dv=parameter,
					between=betweens,
					detailed=True)

		# Add Info of what was compared to ANOVA result
		aov = pd.concat([aov, pd.DataFrame({
			'Index':['Parameter', float('nan')],
			'Value':[parameter, float('nan')]
			})], axis=0, ignore_index=False)

		
		# === Do Post-hoc ===
		def generate_combinations(_list):
			comb_list = list(combinations(_list, len(_list) - 1))
			result = []
			for comb in comb_list:
				excluded_item = list(set(_list) - set(comb))[0]
				result.append({'groups': list(comb), 'between': excluded_item})
			return result

		phoc=[]
		groups = generate_combinations(param_cols)
		for g in groups:
			try:
				for group, gdf in ldf.groupby(g['groups']):
					# Do the test
					# Rename the 'Value' column to the parameter name
					gdf.rename(columns={'Value':parameter}, inplace=True)
					ph=pg.pairwise_tukey(data=gdf, dv=parameter, between=g['between'])
					# Append groups and info to test
					_g=pd.DataFrame(list(group)+[parameter],index=g['groups']+['Parameter']).T
					ph=pd.concat([_g,ph], axis=1, ignore_index=False)
					ph[g['groups']+['Parameter']]=ph[g['groups']+['Parameter']].ffill()
					phoc.append(ph)
			except Exception as e:print(f"PostHoc ERROR: {e}")

		Stats.update({parameter:{'ANOVA':aov,'POSTHOC':phoc}})
	


	# === For each protocol, save Stats results into excel
	# One sheet for ANOVA results
	# One sheet for PostHoc
	fileName=f'{filename}_Stats.xlsx'
	writer = pd.ExcelWriter(fileName, engine='xlsxwriter')
	for param, stats in Stats.items():
		for test in ['ANOVA', 'POSTHOC']:
			row=0
			if type(stats[test]) is not list:
				stats[test]=[stats[test]]
			for exdf in stats[test]:
				exdf.to_excel(writer, sheet_name=f"{param}_{test}".replace('/','_'), startrow=row , startcol=0)   
				row+=(len(exdf.index)+3) #3 being space
	
	if _saving is True:
		writer.close()
		print(f'Saved {fileName}')

	return Stats



if __name__ == '__main__':

	df=pd.read_csv(FILENAME)

	# Three-way SHAM CII: P-E * RV-LV * PreHTx-CSS2h-HOPE2h-HOPE8h
	param_cols=['Group','Storage','Heart','Time']
	keep=['CICII_OXPHOS']
	df=df.loc[:,param_cols+keep]
	print(df)
	
	do_stats(df,
			param_cols=param_cols,
			betweens=param_cols,
			filename=f"{FILENAME.split('.')[0]}Three-way-OXPHOS")

	# # Three-way BSD: Pre vs - CSS vs HOPE at 2h vs HOPE 8h
	# df=df.loc[(df['Group']=='BSD')].drop(columns=['Group', 'Sheep'])
	# print(df)
	# do_stats(df,
	# 		param_cols=['SubGroup','Storage','Heart','Time'],
	# 		betweens=['SubGroup','Storage','Heart','Time'],
	# 		filename=f"{FILENAME.split('.')[0]}_BSD_Storage_Time")


	# # Two-Way within BSD: CSS vs HOPE at 2h
	# df=df.loc[(df['Time']==2)&(df['Group']=="BSD")].drop(columns=['Sheep','Group','SubGroup','Time'])
	# print(df)
	# do_stats(df,
	# 		param_cols=['Storage','Heart'],
	# 		betweens=['Storage','Heart'],
	# 		filename=f"{FILENAME.split('.')[0]}_BSD_2h")


	# # Three-way SHAM vs BSD - CSS vs HOPE at 2h
	# df=df.loc[(df['Time']==2)].drop(columns=['Sheep','SubGroup','Time'])
	# print(df)
	# do_stats(df,
	# 		param_cols=['Group','Storage','Heart'],
	# 		betweens=['Group','Storage','Heart'],
	# 		filename=f"{FILENAME.split('.')[0]}_2h")

	# # Analysis of Non-HTx group: Effect of BSD vs SHAM
	# df=df.loc[df['Storage']!='Non-HTx'].drop(columns=['Sheep','SubGroup','Storage','Time'])
	# do_stats(df,
	# 		param_cols=['Group','Heart'],
	# 		betweens=['Group','Heart'],
	# 		filename=f"{FILENAME.split('.')[0]}_Non-HTx")

