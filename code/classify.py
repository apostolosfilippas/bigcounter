from itertools import combinations
import openpyxl, os , re
minn, maxx, conf = 2 , 18 , '0.05' #0.05,0.11
folder = 'indexes' #[indexes,indexes2]
cachedStopwords = ['i','me','my','myself','we','our','ours','ourselves','you','your','yours','yourself','yourselves','he','him','his','himself','she','her','hers','herself','it','its','itself','they','them','their','theirs','themselves','what','which','who','whom','this','that','these','those','am','is','are','was','were','be','been','being','have','has','had','having','do','does','did','doing','a','an','the','and','if','or','because','as','until','while','of','at','by','for','with','about','into','through','during','before','after','to','from','in','out','on','off','then','there','when','where','why','how','both','so','than','s','t','can','will']
default=-1
policy = 'biggestMatch' # 'allMatchings','biggestMatch'
experiments = ['50000', '100000', '200000', '400000', '800000', '1600000', '3200000', '6400000', '12800000', '25600000', 'full']
target = 'resultsTemp'

# READ FROM THE EXCEL FILES
xlE = openpyxl.load_workbook('Easy.xlsx')
xlH = openpyxl.load_workbook('Hard.xlsx')
test = {}
test['Easy']={'Books':[], 'Restaurants':[], 'Hotels':[]}
test['Hard']={'Books':[], 'Restaurants':[], 'Hotels':[]}
ratings= {'D':-1, 'N':0, 'P':1}
for hardness in ['Easy','Hard']:
    for kind in ['Books']: #['Books','Restaurants','Hotels']
        if hardness=='Easy': 
            sheet = xlE.get_sheet_by_name(kind)
        if hardness=='Hard':
            sheet = xlH.get_sheet_by_name(kind)
        for i in range(1,501 if hardness=='Easy' else 601):
            #replace non  alphanumerical
            text = sheet['A'+str(i)].value
            text = re.sub('\'',' ',text).lower()
            text = ' '.join(re.sub(r'\W+', ' ', text).split())
            rating = ratings[sheet['B'+str(i)].value]
            test[hardness][kind].append([text, rating ] )
patterns={}
transl = {'book':'Books', 'restaurant':'Restaurants', 'hotel':'Hotels'}
for kind in ['book']: #['hotel', 'restaurant', 'book']
    for experiment in experiments:  
        if experiment=='25600000' and kind!='hotel': continue
        for policy in ['allMatchings']: #['allMatchings','biggestMatch']
            for default in ['-1']: #['-1','0','1']
                for L in range(minn,maxx+1):
                    del patterns
                    patterns = {}
                    with open(kind+'-'+folder+'/'+str(experiment)+'/'+conf+'accepted'+str(L)+'.txt',encoding='utf-8',mode='r') as f:
                        [num, prob] = [float(k) for k in f.readlines()[-1].split()[1:3]]
                    with open(kind+'-'+folder+'/'+str(experiment)+'/'+conf+'accepted'+str(L)+'.txt',encoding='utf-8',mode='r') as f:                                
                        for line in f:
                            try:
                                [key, li] = line.split(':')
                            except ValueError:
                                continue
                            li = eval(li)
                            if li[1]> sum(li)*prob:
                                patterns[key] = 1
                            else:
                                patterns[key]=0                  
                    for hardness in ['Easy','Hard']:
                        if L==minn and hardness=='Easy': print(kind+'--'+str(experiment)+'--'+str(policy)+'--'+str(default)) 
                        results = []
                        #---for every sentence in the test test
                        for entry in test[hardness][transl[kind]]:
            
                            #---get subsequences
                            sentence,rating= entry[0].split(),entry[1]
                            sentenceTemp = entry[0]
                            if len(sentence)!=L: continue
                            for i in range(0,len(sentence)):
                                if sentence[i] in cachedStopwords:
                                        sentence[i]=1
                            counter2 = -1
                            tempFound = list()
                            for i in range(0,len(sentence)):
                                if sentence[i]==1:
                                    continue
                                counter2 += 1
                                #creating subsequences
                                prefix = sentence[:i+1]
                                subsentence = sentence[i+1:]
                                subseq = [word for word in subsentence if word != 1]
                                for j in range(0, len(subseq)+1):
                                    for combo in combinations(subseq,j):
                                        suffix = subsentence[:]
                                        counter3 = 0
                                        for k in range(0,len(suffix)):
                                            if counter3 == len(combo):
                                                break
                                            if suffix[k] == combo[counter3]:
                                                suffix[k]=0
                                                counter3 +=1
                                        tempFound.append(str(tuple(prefix+suffix)))
                                sentence[i]=0
                            if policy=='allMatchings':
                                #--- CLASSIFY -- way 1 / find all matchings 
                                length = len(sentence)
                                foundC = []
                                for k in tempFound:
                                    if k in patterns:
                                        foundC.append(patterns[k])
                                    else:
                                        foundC.append(-1)
                                #weighted coverage
                                P = sum([1 for k in foundC if k==1])
                                N = sum([1 for k in foundC if k==0])               
                                if P>N:
                                    classified=1 
                                elif N>P:
                                    classified=0
                                else:
                                    classified=default #predict 1 instead of -1 if no matches
                                results.append(str(rating)+'\t'+str(classified)+'\t'+sentenceTemp     )
                            elif policy == 'biggestMatch':
                                #---CLASSIFY -- way 2 / the biggest matching
                                classified=-1
                                for k in tempFound:
                                    if k in patterns:
                                        classified = patterns[k]
                                        break   
                                if classified==-1: classified = default #default is -1 
                                results.append(str(rating)+'\t'+str(classified)+'\t'+sentenceTemp     )      
                                
                        # STORE ----
                        if not os.path.exists(target): os.makedirs(target)
                        if L==2:
                            with open(target+'/'+kind+'_'+hardness+'_'+str(experiment)+'_nocursor_'+policy+'-'+str(default)+'.txt',encoding='utf-8', mode='w') as g:
                                g.write( '\n'.join(results)    )
                        else:
                            with open(target+'/'+kind+'_'+hardness+'_'+str(experiment)+'_nocursor_'+policy+'-'+str(default)+'.txt',encoding='utf-8', mode='r') as f:
                                temp = f.read().split('\n')
                            with open(target+'/'+kind+'_'+hardness+'_'+str(experiment)+'_nocursor_'+policy+'-'+str(default)+'.txt',encoding='utf-8', mode='w') as g:
                                g.write( '\n'.join(temp+results)  )
                        #print accuracy per sentence length
                        rcounter = 0
                        for m in results:
                            if m.split('\t')[0]==m.split('\t')[1]:
                                rcounter+=1
                        if len(results)==0: 
                            print(hardness+'-'+str(L)+'-no sentences')
                        else:
                            print(hardness+'-'+str(L)+'-Acc = '+str(rcounter/len(results)))
                for hardness in ['Easy','Hard']:
                    with open(target+'/'+kind+'_'+hardness+'_'+str(experiment)+'_nocursor_'+policy+'-'+str(default)+'.txt',encoding='utf-8', mode='r') as f:
                        temp = f.read().split('\n')
                    temp = [k for k in temp if len(k)>0]
                    temp = [k.split('\t') for k in temp]
                    temp1 = [1 if k[0]==k[1] else 0  for k in temp]
                    if len(temp)>0:            
                        print(hardness+' -- TOTAL ACC = '+str(sum(temp1)/len(temp)))
                    else:
                        print(hardness+' -- TOTAL ACC = NaN')
                    for i in range(-1,2):
                        temp2 = [k for k in temp if k[0]==str(i)]
                        temp1 = [1 if k[0]==k[1] else 0  for k in temp2]
                        print(hardness+' -- '+str(i)+ ' ACC = '+str(sum(temp1)/len(temp2)))