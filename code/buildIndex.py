"""
@author: apostolosfilippas
Input: 
-  'Reviews.txt' a file where every line begins with a star rating (number in [1,5]) 
                 followed by the lowercased space-separated review. 
                 e.g. '1 what a scum' or '1\twhat a scum'
Output:
-   at folder 'index', easy to understand.
Params:
-   minn,maxx   deal with reviews with lengths in [minn,maxx]
-   maxConf     how many confidence intervals to consider (from table conf)
-   chunk       how many chunks to break the original big file to. Higher chunk
                makes code faster but needs more memmory. Adjust accordingly.
"""
from itertools import combinations
import scipy.stats as sci
import numpy as np
import os

#deals with sentences of len [minn,maxx]. How big chunks to break down when building index
minn, maxx, chunk, kind = 2, 10, 2000000, 'hotel'
conf =[0.05,3.841] #confidence interval and its corresponding x^2-statistic
cachedStopwords = ['i','me','my','myself','we','our','ours','ourselves','you','your','yours','yourself','yourselves','he','him','his','himself','she','her','hers','herself','it','its','itself','they','them','their','theirs','themselves','what','which','who','whom','this','that','these','those','am','is','are','was','were','be','been','being','have','has','had','having','do','does','did','doing','a','an','the','and','if','or','because','as','until','while','of','at','by','for','with','about','into','through','during','before','after','to','from','in','out','on','off','then','there','when','where','why','how','both','so','than','s','t','can','will']


#works by sentence lengths
for length in range(minn,maxx+1):
    print('------- length='+str(length))
    foundNumber, accepted, sentences, total = 0, dict(), list(), [0,0]
    #==========================================================================  
    #breaks down the file into subfiles. Only keeps reviews w. rating 1,2->negative 4,5->positive 
    print('Getting sequences')
    with open('Reviews-'+kind+'.txt','r') as f:
        for sentence in f:
            if len(sentence[1:].split())!=length or sentence[0]=='3': continue
            else:
                    temp = sentence[1:].split()
                    counter = 0
                    for i in range(0,len(temp)):
                        if temp[i] in cachedStopwords:
                            counter +=1
                            temp[i]=1
                    if counter == len(temp): continue 
                    rating = int(sentence[0])
                    if rating == 1 or rating ==2:
                        rating = 1
                        total[0]+=1
                    else:
                        rating = 5
                        total[1]+=1
                    sentences.append([rating, temp])    
    #========================================================================== 
    print('Creating index')
    index = dict()
    powersoftwo = dict()    
    #we'll be using them again and again it makes sense to keep them stored
    for i in range(0,length):
        powersoftwo[i] = 2**i     
    #we don't need to create subsenqs this time, just do the math
    #we try to find how many subsequences begin by each distinct word. 
    #e.g. in the sentence: "i will never go back" the subseqences
    #(1, 1, 'never', 'go', 'back'),(1, 1, 'never', 0, 'back'), (1, 1, 'never', 'go', 0), (1, 1, 'never', 0, 0)
    #all begin with 'never', hence we add 4 to the #subseqs beginning with "never"
    for entry in sentences:
        subsentence = [ i for i in entry[1] if i!=1]
        counter = 1
        for word in subsentence:
            if word in index:
                index[word] += powersoftwo[len(subsentence)-counter]
            else:
                index[word] = powersoftwo[len(subsentence)-counter]
            counter +=1
    del counter    
    #remove words that only appeared once but keeps them in the count
    index2 = dict()
    for entry in index:
        if index[entry]>1:
            index2[entry]=index[entry]
    foundNumber = len(index)-len(index2)
    index = sorted(index2.items(), key=lambda x: x[1], reverse=True)
    del index2    
    #==========================================================================
    print('Performing Statistical Pruning')
    summ = sum(total)
    total[0] = total[0]/summ
    total[1] = 1 - total[0]
    print('   Probabilities = '+str(total))    
    #creates and stores a preprocessed list which will considerably speed things up
    print('   Creating Preprocessed List')
    preprocessed= dict()
    for i in range(0,100):
            for j in range(0,100):
                if i == 0 and j == 0:
                    continue                    
                if (i+j)<20 and i <5:
                    a = sci.binom_test(i,i+j, total[0])
                    if a<=conf[0]:
                        preprocessed[(i,j)] = 1
                    else:
                        preprocessed[(i,j)] = 0 
                else:
                    a = sci.chisquare(np.array([i,j]), np.array([ total[0]*(i+j), total[1]*(i+j)]))[0]
                    if a>=conf[1]:
                        preprocessed[(i,j)] = 1
                    else:
                        preprocessed[(i,j)] = 0    
    #doing chunking in a greedy way that works! 
    #Now what we want to do is since we have too many subsequences, break them down in chuncks.
    # for example we first want to work only on all subsequences starting with 'never' or 'bad' (or whatever)
    # so we go back to our sentences and get all of these subsequences
    summ = 0
    dictio = dict()
    dictList = list()
    for entry in index:
        dictio[entry[0]]=entry[1]
        summ += entry[1]
        if summ > chunk:
            dictList.append(dictio)
            summ = 0
            dictio=dict()
    if summ >0:
        dictList.append(dictio)
    del dictio
    del index    
    #For each dictio, we will extract the subsequences and do the statistical 
    #pruning. This way we don't have to compare!
    counter=0
    for dictio in dictList:
        #start = timeit.default_timer()
        counter+=1
        found = dict()
        print('   working on '+str(counter)+' out of '+str(len(dictList)))
        #first we create all of the subsequences and store them in found
        for entry in sentences:
            sentence = entry[1][:]
            rating = entry[0]
            length2 = len([word for word in sentence if word!=1])
            counter2 = -1
            tempFound = list()
            for i in range(0,len(sentence)):
                if sentence[i]==1:
                    continue
                counter2 += 1
                if sentence[i] not in dictio:
                    sentence[i]=0
                    continue                
                #when we have lots of entries with value two this will make it faster
                dictio[sentence[i]] = dictio[sentence[i]] - powersoftwo[length2-counter2-1]
                if dictio[sentence[i]]==0:
                    del dictio[sentence[i]]
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
                        tempFound.append(tuple(prefix+suffix))
                sentence[i]=0
            for seq in tempFound:
                if seq in found:
                    if rating==1:
                        found[seq][0] +=1
                    else:
                        found[seq][1] +=1
                else:
                    found[seq] = [0,0]
                    if rating==1:
                        found[seq][0] +=1
                    else:
                        found[seq][1] +=1
        foundNumber += len(found)
        #Now we perform the statistical pruning

        for entry in found:
                    if found[entry][0] in range(0,100) and found[entry][1] in range(0,100):
                        if preprocessed[(found[entry][0],found[entry][1])] == 1:
                            accepted[entry] = found[entry]
                        continue
                        
                    if sum(found[entry]) < 20 and found[entry][0] < 5:
                            if sci.binom_test(found[entry][0],sum(found[entry]), total[0]) <= conf[0]:
                               accepted[entry] = found[entry]
                    else:
                        if sci.chisquare(np.array(found[entry]), np.array([i*sum(found[entry]) for i in total]))[0] >= conf[1]:
                            accepted[entry] = found[entry]
        #stop = timeit.default_timer()
        #print(stop-start)
    #==========================================================================
    print('Storing') 
    if not os.path.exists('index'):
        os.mkdir('index')
    with open('index/'+str(conf[0])+'accepted'+str(length)+'.txt','w') as f:
        for entry in accepted:
            f.write(str(entry) + ':' + str(accepted[entry])+'\n' )
        f.write(str(foundNumber) + ' ' + str(len(accepted))+ ' '+str(total[1])[:5])
