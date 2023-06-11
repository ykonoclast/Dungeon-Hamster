from browser import document, console, window, html, alert, worker
from bisect import bisect_right
from queue import Queue
import javascript

#from itertools import izip

#TODO ajouter en var globales les noms de classes css en cas de changement
DB_NAME="DungeonDB"
DB_VERSION=1
MSG_RESTART="restart"
#TODO : ci-dessous voir si namedtuples pas meilleur
list_mvt=[{"turn": 120,"round": 40}, {"turn": 90,"round": 30}, {"turn": 60,"round": 20}, {"turn": 30,"round": 10}, {"turn": 15,	"round": 5}, {"turn": 0,"round": 0}]
list_enc_thresh=[0, 401, 801, 1201, 1601, 2401]

list_active_sections = [x.id for x in document.getElementsByClassName("Active_Section")]
list_inactive_sections = [x.id for x in document.getElementsByClassName("Inactive_Section")]

#TODO supprimer les alertes et mieux logger


#SECTION fonctions utilitaires
def get_section(elt):
	name=""
	current_node=elt
	while name != "SECTION":
		current_node=current_node.parent
		name=current_node.nodeName
	#TODO exception : si pas dans section
	return current_node

def get_row_info(cellule):
	row = cellule.parent
	row_index=row.rowIndex
	tbody = row.parent
	table = tbody.parent
	nbrows=table.rows.length#TODO ne peut on passer par le tbody au lieu d'interroger la table et les rows de la table?
	return tbody, nbrows, row_index, row








#SECTION : persistance des données
db = 0

def disp_persist(granted):#TODO remplacer ces alertes de merde par des logs
	if granted:
		alert("Storage will persist and not be cleared")
	else:
		alert("Storage won’t persist and may be cleared")

navigator = window.navigator
if hasattr(navigator, "storage") and hasattr(navigator.storage,"persist"):
	navigator.storage.persist().then(disp_persist)
else:
	alert("Go fuck yourself")
	
def upgradeDB(event):#base de données de nom inconnu ou de version n'existant pas : on construit le schéma
	#TODO supprimer anciennes version
	db = event.target.result#event.target est la REQUÊTE IndexedDb ; ici le résultat de la requête (d'ouverture) est la base elle-même

	for section in list_active_sections+list_inactive_sections:#on crée un store par section
		objectStore = db.createObjectStore(section, { "autoIncrement": True })#store sans index (on n'interrogera jamais sur les colonnes), autoincrement pour clé technique autoconstruite (car on peut pas utiliser rowindex : il change avec suppressions) ou de keypath ; voir la doc : beaucoup d'implications sur les keypath et les keygenerators (notamment uniquement objets JS si keypath)

def open_db(withVersion):
	if withVersion:
		dbrequest = window.indexedDB.open(DB_NAME,DB_VERSION)
	else:
		dbrequest = window.indexedDB.open(DB_NAME)
	dbrequest.bind("upgradeneeded", upgradeDB)
	dbrequest.bind("success", when_db_opened)

def restore_section(e):
	sec_id = e.target.sec_id
	result = e.target.result
	for r in result:
		dicti=javascript.JSObject.to_dict(r)
		console.log(f"RESTORE : {dicti}")




def when_db_opened(event):#sera forcément appelé après upgraDB car l'event success arrive toujours après le traitement de upgradeneeded
	version = event.target.result.version

	if version != DB_VERSION:#TODO commenter plus, mais en gros c'est la vieille version et on la supprime
		event.target.result.close()
		window.indexedDB.deleteDatabase(DB_NAME)
		open_db(True)
	else :#setup from DB
		global db #pour affecter à la variable globale et pas en créer une local avec l'affectation qui suit
		db = event.target.result;
		#const objectStore = db.transaction("customers").objectStore("customers")
		transaction = db.transaction(list_active_sections,"readonly")
		for section in list_active_sections:
			console.log(f"OPENING STORE {section}")
			store = transaction.objectStore(section)
			strequest = store.getAll()
			strequest.sec_id=section
			strequest.bind("success",restore_section)








#Ouverture de la base de données
if hasattr(window,"indexedDB"):
	open_db(False)#TODO commenter pourquoi le false et la méthode appelée









def del_row_db(sec_id,dbkey):
	if db!=0:#la requête d'ouverture est passée
		transaction = db.transaction(sec_id,"readwrite")#on limite la transaction au store d'intérêt pour pers
		store = transaction.objectStore(sec_id)
		console.log(f"erasing in DB key {dbkey} in store {sec_id}")
		store.delete(dbkey)#TODO binder callback de succès et échec pour log









#gestion du timer de 5s après frappe d'une touche dans un champ pour limiter les appels BD



#TODO commenter et expliquer ce que l'on fait ici
def write_key_in_row(e):
	console.log(f"in wkir e={e}")
	row = e.target.row_persisted
	row.dbkey = e.target.result

def create_datapack(row):
	obj_cell = row.getElementsByClassName("Col_Obj")[0]
	obj_text = obj_cell.text
	enc_cell = row.getElementsByClassName("Col_Enc")[0]
	enc_text = enc_cell.text
	data = {"obj": obj_text,"enc": enc_text}
	return data

def when_typing_done(row_desc):
	#tbody,nbrows,index,row=get_row_info(cellule)
	#section = get_section(cellule)
	#sec_id = section.id


	sec_id = row_desc["section"]
	dbkey=row_desc["dbkey"]

	section = document[sec_id]
	rows = section.getElementsByTagName("TR")
	row=0
	for r in rows:
		if hasattr(r,"dbkey"):#un row persisté
			if r.dbkey==dbkey:
				row=r

	if row!=0:#le row dont le timer vient d'expirer est toujours bien là
		if db!=0:#la requête d'ouverture est passée
			data = create_datapack(row)
			console.log(f"updating in DB {data} in store {sec_id} with key {dbkey}")
			transaction = db.transaction(sec_id,"readwrite")#on limite la transaction au store d'intérêt pour pers
			store = transaction.objectStore(sec_id)
			store.put(data,row.dbkey)#TODO binder callback de succès et échec pour log




		#TODO DECOMMENTER!!!!
		#

		#if hasattr(row,"dbkey"):#le row est déjà persisté, on update
		#	console.log(f"updating in DB {data} in store {sec_id} with key {row.dbkey}")
		#	store.put(data,row.dbkey)#TODO binder callback de succès et échec pour log
		#else:#le row n'a jamais été persisté, on ajoute
		#	console.log(f"adding in DB {data} in store {sec_id}")
		#	req = store.add(data)#TODO binder callback d'échec pour log et logger plus dans celle de succès
		#	req.row_persisted = row #(IMPORTANT) l'objet sur lequel on binde EST le target passé à la callback DONC on ajoute à la requête un attribut : le row, comme cela la clé générée pourra y être inscrite dans la callback
		#	req.bind("success", write_key_in_row)


worker_dict = {}#TODO initialiser avec la liste des section et mutualiser le code avec la création de la base (ATTENTION : pas initialiser au même endroit car on ne maîtrise pas le temps de création de la base)
worker_queue = Queue()

#TODO commenter la procédure d'enregistrement
def worker_ready(new_worker):
	#TODO cracher une ERREUR si la queue ne possède pas un machin
	row_desc=worker_queue.get()
	new_worker.send(row_desc)
	sec_id = row_desc["section"]
	dbkey =row_desc["dbkey"]

	if sec_id not in worker_dict:#la section ne possède aucun row avec worker actif
		dict_entry = {row_desc["dbkey"]:new_worker}
		worker_dict[sec_id]=dict_entry
	else:#la section est déjà dans le dico
		worker_dict[sec_id][dbkey]=new_worker

def worker_message(msg):
	row_desc=msg.data
	sec_id=row_desc["section"]
	dbkey=row_desc["dbkey"]
	console.log(f"worker CALLBACK : date is : section:{sec_id};key:{dbkey}")
	#on supprime le worker du dictionnaire des workers actifs
	if sec_id in worker_dict:
		if dbkey in worker_dict[sec_id]:
			#on fait tous les tests ci-dessus car, si l'utilisateur tape très vite, il peut y avoir plusieurs workers démarrés ou plusieurs timers lancés
			worker_dict[sec_id].pop(dbkey)
	when_typing_done(row_desc)






def when_keyup(e):
	cellule = e.target
	section = get_section(cellule)
	sec_id = section.id
	tbody,nbrows,index,row=get_row_info(cellule)

	#TODO ici et ailleurs (suppression?) exporter à un thread la tache de vérifier ça et de rappeler quand la base est dispo
	if db!=0:#la requête d'ouverture est passée
		transaction = db.transaction(sec_id,"readwrite")#on limite la transaction au store d'intérêt pour pers
		store = transaction.objectStore(sec_id)
		if hasattr(row,"dbkey"):#le row a déjà été historisé
			dbkey = row.dbkey
			create_worker=True

			if sec_id in worker_dict:#on a déjà historisé des rows de cette section
				if dbkey in worker_dict[sec_id]:#le row possède un worker actif
					create_worker=False
					if worker_dict[sec_id][dbkey]!=0:#le worker est déjà initialisé, on peut donc le relancer (sinon c'est inutile, on attend juste)
						timer_worker = worker_dict[sec_id][dbkey]
						console.log("ENVOI MSG RESTART")
						timer_worker.send(MSG_RESTART)

			if create_worker:#pas de worker actif, on le crée
				row_desc={"section":sec_id,"dbkey":dbkey}#TODO faire un namedtuple plutôt ici
				worker_queue.put(row_desc)
				console.log("CREATION WORKER")
				worker.create_worker("timerworker", worker_ready, worker_message)

				#on signale maintenant qu'un worker est en train de s'initialiser, pour ne pas risquer d'en créer un deuxième avant que le premier n'ait complètement démarré
				if sec_id not in worker_dict:
					dict_entry = {row_desc["dbkey"]:0}
					worker_dict[sec_id]=dict_entry
				else:#la section est déjà dans le dico
					worker_dict[sec_id][dbkey]=0

		else:#le row n'a jamais été historisé, on va le créer pour avoir une clé
			data = create_datapack(row)
			console.log(f"adding in DB {data} in store {sec_id}")
			req = store.add(data)#TODO binder callback d'échec pour log et logger plus dans celle de succès
			req.row_persisted = row #(IMPORTANT) l'objet sur lequel on binde EST le target passé à la callback DONC on ajoute à la requête un attribut : le row, comme cela la clé générée pourra y être inscrite dans la callback
			req.bind("success", write_key_in_row)



#SECTION : gestion écartement entre barre du bas et reste du contenu (car la position fixe enlève du flux et empêche donc de scroller assez pour voir tout le tableau le plus bas)
def set_main_padding(*args):#pour avoir des arguments à volonté, comme on ne l'appelle pas forcément avec l'event e (au premier appel au chargement)
	height=document["main_recap_id"].height
	main=document["main_id"]
	#main prend un padding car mettre de la marge à l'Inv_Area ne marchera pas : la marge n'est calculée que si un élément suit, or la barre est fixed donc hors flux
	#on ajoute 1rem au padding car ainsi ça décolle un peu plus
	main.style.paddingBottom=f"calc({height}px + 1rem)"

#on appelle une première fois la fonction d'écartement au chargement de la page
set_main_padding()
#on la binde au redimmensionnement de la fenêtre
window.bind('resize', set_main_padding)

#SECTION gestion des valeurs numériques
def get_speeds(enc):
	index=bisect_right(list_enc_thresh,enc)-1#bisect_right retourne l'indice de l'élément qui devrait suivre enc si celui-ci était inséré et que la liste devait rester trier, on fait -1 et cela sélectionne donc la valeur immédiatement inférieure à enc
	return list_mvt[index]

def get_section_enc(id):
	#TODO execption si id existe pas
	recap = document[id]
	sec_tot = recap.getElementsByClassName("Sec_Tot")[0]
	return int(sec_tot.text)

def update_main_recap():
	sacdos=get_section_enc("recap_sacdos_id")
	grossac=get_section_enc("recap_grossac_id")
	bourse=get_section_enc("recap_bourse_id")
	petitsac1=get_section_enc("recap_petitsac1_id")
	petitsac2=get_section_enc("recap_petitsac2_id")
	petitsac3=get_section_enc("recap_petitsac3_id")
	porte=get_section_enc("recap_porte_id")

	total = sacdos + grossac + bourse + petitsac1 + petitsac2 + petitsac3 + porte
	sanssacdos = total - sacdos
	sanssacsclass = total - petitsac1 - petitsac2 - petitsac3 - grossac
	justebourseporte = porte + bourse

	document["total_id"].text=total
	document["sanssacdos_id"].text=sanssacdos
	document["sanssacsclass_id"].text=sanssacsclass
	document["justebourseporte_id"].text=justebourseporte

	total_speed_byturn, total_speed_byround = get_speeds(total).values()
	sanssacdos_speed_byturn, sanssacdos_speed_byround = get_speeds(sanssacdos).values()
	sanssacsclass_speed_byturn, sanssacsclass_speed_byround = get_speeds(sanssacsclass).values()
	justebourseporte_speed_byturn, justebourseporte_speed_byround = get_speeds(justebourseporte).values()

	document["total_byround_id"].text=total_speed_byround
	document["sanssacdos_byround_id"].text=sanssacdos_speed_byround
	document["sanssacsclass_byround_id"].text=sanssacsclass_speed_byround
	document["justebourseporte_byround_id"].text=justebourseporte_speed_byround

	document["total_byturn_id"].text=total_speed_byturn
	document["sanssacdos_byturn_id"].text=sanssacdos_speed_byturn
	document["sanssacsclass_byturn_id"].text=sanssacsclass_speed_byturn
	document["justebourseporte_byturn_id"].text=justebourseporte_speed_byturn

def update_enc(section):
	#calcul du contenu de l'emplacement
	sec_enc=section.getElementsByClassName("Sec_Enc")[0]
	list_enc=section.getElementsByClassName("Col_Enc")

	items_total = sum(int(x.text) for x in list_enc if x.text.isnumeric())
	sec_enc.text=items_total

	#prise en compte de l'encombrement intrinsèque
	enc_intr=0
	list_sec_intr=section.getElementsByClassName("Sec_Intr")
	if list_sec_intr:#liste non vide : il y a donc une valeur intrinsèque pour cet emplacement
		sec_intr=list_sec_intr[0]
		enc_intr=int(sec_intr.text)

	#affichage du total
	sec_tot = section.getElementsByClassName("Sec_Tot")[0]
	sec_tot.text=items_total+enc_intr

	#validation des entrées
	color=""#comme cela, si aucun cas, la couleur redevient par défaut
	if items_total!=0:
		list_sec_max=section.getElementsByClassName("Sec_Max")
		color="MediumSpringGreen"
		if list_sec_max:
			sec_max=list_sec_max[0]
			maxi=int(sec_max.text)
			if items_total>maxi:
				color="red"

	sec_enc.style.color=sec_tot.style.color=color

	#mise à jour du récap total en bas
	update_main_recap()

#SECTION creation et suppression des rows des tables
def make_new_row(tbody):
	new_row=html.TR()
	cell_obj=html.TD(Class="Col_Obj", contenteditable="true")
	cell_enc=html.TD(Class="Col_Enc", contenteditable="true", inputmode="decimal")
	cell_del=html.TD("✖",Class="Col_Del")
	#on binde les mêmes listeners que pour les cellules de base
	cell_obj.bind("input",when_obj_changed)
	cell_obj.bind("keyup",when_keyup)
	cell_enc.bind("input",when_enc_changed)
	cell_enc.bind("keyup",when_keyup)
	cell_del.bind('click',when_del_clicked)
	new_row.appendChild(cell_obj)
	new_row.appendChild(cell_enc)
	new_row.appendChild(cell_del)
	tbody.appendChild(new_row)

def del_row(cellule):
	tbody,nbrows,index,row=get_row_info(cellule)
	section=get_section(cellule)
	row.remove()
	if index<2 and nbrows<3 or index==nbrows-1:#première et unique ligne ou dernière, on la recrée immédiatement
		#TODO voir si on peut tout de même pas THEAD et modifier alors ces valeurs d'index (avec tbody plutôt que table dans le css)
		make_new_row(tbody)
	update_enc(section)

	if hasattr(row, "dbkey"):#le row est persisté, il faut le supprimer de la base
		del_row_db(section.id, row.dbkey)

def check_row_todel(cellule, is_enc_col):
	row=cellule.parent
	other_class_name="Col_Obj" if is_enc_col else "Col_Enc"
	other_cell=row.getElementsByClassName(other_class_name)[0]
	if other_cell.text:
		if is_enc_col:
			update_enc(get_section(cellule))
			cellule.style.background=None
	else:
		del_row(cellule)

def when_del_clicked(e):
	del_row(e.target)

list_col_del=document.getElementsByClassName("Col_Del")
for i in list_col_del:
	if (get_section(i).class_name=="Active_Section"):
		i.bind('click',when_del_clicked)

#SECTION gestion du remplissage des rows des tables
def validate_enc(cellule):
	list_BR=cellule.getElementsByTagName("BR")
	for i in list_BR:#suppression des sauts de ligne
		i.remove()
	texte_saisi=cellule.text

	if texte_saisi.isnumeric():
		cellule.style.background="MediumSpringGreen"
		tbody, nbrows, row_index, trash=get_row_info(cellule)
		if(row_index==(nbrows-1)):#on est en train de remplir l'enc de la dernière ligne, il faut donc en rajouter une
			make_new_row(tbody)
	else:
		if texte_saisi:
			cellule.style.background="red"
	
	update_enc(get_section(cellule))#on appelle toujours l'update de l'enc car on peut avoir rendu non-numérique une cellule l'étant antérieurement

def check_text_changed(e,is_enc_col):
	cellule = e.target
	if cellule.text:
		if is_enc_col:
			validate_enc(cellule)
	else:
		check_row_todel(cellule,is_enc_col)

def when_obj_changed(e):
	check_text_changed(e, False)

def when_enc_changed(e):
	check_text_changed(e,True)

list_col_enc=document.getElementsByClassName("Col_Enc")
for i in list_col_enc:
	i.bind("input",when_enc_changed)
	i.bind("keyup",when_keyup)

list_col_obj=document.getElementsByClassName("Col_Obj")
for i in list_col_obj:
	i.bind("input",when_obj_changed)
	i.bind("keyup",when_keyup)

#SECTION Gestion de l'activation/inactivation des sections
def when_checkbox_clicked(e):
	case=e.target
	section=get_section(case)
	list_td=section.getElementsByTagName("TD")
	sec_tot = section.getElementsByClassName("Sec_Tot")[0]
	sec_enc = section.getElementsByClassName("Sec_Enc")[0]
	for td in list_td:
		if case.checked:
			section.class_name="Active_Section"
			if td.class_name=="Col_Del":
				td.bind('click',when_del_clicked)
			else:
				td.setAttribute("contenteditable", True)
				if td.class_name=="Col_Enc":
					td.setAttribute("inputmode","numeric")
					validate_enc(td)
		else:
			section.class_name="Inactive_Section"
			if td.class_name=="Col_Del":
				td.unbind('click',when_del_clicked)
			else:
				td.setAttribute("contenteditable", False)
				if td.class_name=="Col_Enc":
					td.style.background="transparent"
			sec_enc.style.color=sec_tot.style.color="#888"

			#neutralisation de l'encombrement
			sec_tot.text=0
			update_main_recap()


list_checkboxes=document.getElementsByTagName("INPUT")
for i in list_checkboxes:
	i.bind('click',when_checkbox_clicked)