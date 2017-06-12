import unittest
import sys
# so we import local stk before any other
sys.path.insert(0,"../../")
from stk.stk_trees import import_tree, import_trees, trees_equal, tree_contains, assemble_tree_matrix
from stk.stk_trees import delete_taxon, sub_taxon, permute_tree, getTaxa
import numpy
import os
from lxml import etree
import stk.p4 as p4
# our test dataset
import tempfile

standard_tre = "data/input/test_tree.tre"
single_source_input = "data/input/single_source.phyml"
expected_tree = '((Taxon_c:1.00000,(Taxon_a:1.00000,Taxon_b:1.00000)0.00000:0.00000)0.00000:0.00000,(Taxon_d:1.00000,Taxon_e:1.00000)0.00000:0.00000)0.00000:0.00000;'
parser = etree.XMLParser(remove_blank_text=True)

# To run a single test:
# python -m unittest _trees.TestImportTree.test_permute_trees

# Test the loading and saving of trees files in various forms
class TestImportExportTree(unittest.TestCase):

    def test_import_quoted_tree(self):
        test_file = "data/input/quoted_taxa.tre"
        e_tree = "(('Taxon (c)', (Taxon_a, Taxon_b)), (Taxon_d, Taxon_e));"
        tree = import_tree(test_file)
        self.assert_(trees_equal(e_tree,tree))

    def test_import_tutorial_tree(self):
        test_file = "../../doc/tutorial/5.3_DataEntry/HallThatje_2009.tre"
        e_tree = "((Aegla_sp., (Pagurus_bernhardus, Pagurus_hirsutiusculus)), (((Cryptolithodes_sitchensis, Cryptolithodes_typicus), (Phyllolithodes_papillosus, (Lopholithodes_mandtii, (Glyptolithodes_cristatipes, (Paralomis_formosa, Paralomis_spinosissima))), (Neolithodes_brodiei, (Paralithodes_camtschaticus, Paralithodes_brevipes), (Lithodes_confundens, Lithodes_ferox)))), (Oedignathus_inermis, (Hapalogaster_dentata, Hapalogaster_mertensii))));"
        tree = import_tree(test_file)
        self.assert_(trees_equal(e_tree,tree))

    def test_import_treeview(self):
        test_file = "data/input/treeview_test.tre"
        tree = import_tree(test_file)
        expected_tree = "((Taxon_c, (Taxon_a, Taxon_b)), (Taxon_d, Taxon_e));"        
        self.assert_(trees_equal(expected_tree,tree))

    def test_import_mesquite(self):
        test_file = "data/input/mesquite_test.tre"
        expected_tree = "((Taxon_c, (Taxon_a, Taxon_b)), (Taxon_d, Taxon_e));" 
        tree = import_tree(test_file)
        self.assert_(trees_equal(expected_tree,tree))

    def test_import_figtree(self):
        test_file = "data/input/figtree_test.tre"
        tree = import_tree(test_file)
        expected_tree = "((Taxon_c, (Taxon_a, Taxon_b)), (Taxon_d, Taxon_e));" 
        self.assert_(trees_equal(expected_tree,tree))

    def test_import_dendroscope(self):
        test_file = "data/input/dendroscope_test.tre"
        tree = import_tree(test_file)
        expected_tree = "((Taxon_c:1, (Taxon_a:1, Taxon_b:1):0):0, (Taxon_d:1, Taxon_e:1):0);" 
        self.assert_(trees_equal(expected_tree,tree))

    def test_import_macclade(self):
        test_file = "data/input/macclade_test.tre"
        tree = import_tree(test_file)
        expected_tree = "((Taxon_c, (Taxon_a, Taxon_b)), (Taxon_d, Taxon_e));" 
        self.assert_(trees_equal(expected_tree,tree))

    def test_import_paup(self):
        test_file = "data/input/paup_tree.tre"
        tree = import_tree(test_file)
        expected_tree = "(Mimodes_graysoni, (Mimus_gilvus, Mimus_polyglottos), ((Mimus_gundlachii, (Nesomimus_macdonaldi, Nesomimus_melanotis, Nesomimus_parvulus, Nesomimus_trifasciatus)), ((Mimus_longicaudatus, ((Mimus_patagonicus, Mimus_thenca), (Mimus_saturninus, Mimus_triurus))), (Oreoscoptes_montanus, (Toxostoma_curvirostre, Toxostoma_rufum)))));" 
        self.assert_(trees_equal(expected_tree,tree))

    def test_utf_tree(self):
        test_file = "data/input/utf_tree.tre"
        trees = import_trees(test_file)
        expected_tree = """(Colletes_skinneri, ((((Melitta_eickworti, Hesperapis_larreae), ('Andrena (Callandrena) sp.', (Panurgus_calcaratus, (Calliopsis_fracta, Calliopsis_pugionis)))), ((Svastra_machaerantherae, Svastra_obliqua), ('Tetraloniella_sp.', (Melissodes_rustica, (Melissodes_desponsa, 'Melissodes_sp.'))))), ((((Dieunomia_heteropoda, Dieunomia_nevadensis), ((Ceratina_calcarata, ((Chelostoma_fuliginosum, (Hoplitis_biscutellae, (Hoplitis_albifrons, Hoplitis_pilosifrons))), (Megachile_pugnata, Coelioxys_alternata))), ((Paranthidium_jugatorium, Anthidiellum_notatum), (Anthidium_oblongatum, Anthidium_porterae)))), ((Oreopasites_barbarae, ((Holcopasites_calliopsidis, Holcopasites_ruthae), (Nomada_maculata, (Nomada_imbricata, Nomada_obliterta)))), ((Leiopodus_singularis, (Xeromelecta_californica, Zacosmia_maculata)), ((Paranomada_velutina, Triopasites_penniger), (Epeolus_scutellaris, ('Triepeolus "rozeni"', Triepeolus_verbesinae)))))), ((Anthophora_furcata, (Anthophora_montana, Anthophora_urbana)), (((Exomalopsis_completa, Exomalopsis_rufiventris), ('Ptilothrix_sp.', (Diadasia_bituberculata, Diadasia_nigrifrons, (Diadasia_diminuta, Diadasia_martialis)))), ((Xylocopa_tabaniformis, Xylocopa_virginica), (Centris_hoffmanseggiae, (Apis_dorsata, (Apis_mellifera, Apis_nigrocincta)), ((Euglossa_imperialis, (Eulaema_meriana, (Eufriesea_caerulescens, Exaerete_frontalis))), ((Bombus_avinoviellus, (Bombus_pensylvanicus, Bombus_terrestris)), ('Melipona_sp.', Scaptotrigona_depilis, Lestrimelitta_limao, (Trigona_dorsalis, Trigona_necrophaga)))))))))));"""
        self.assert_(trees_equal(expected_tree,trees[0]))


    def test_import_tb_tree(self):
        test_file = "data/input/tree_with_taxa_block.tre"
        tree = import_tree(test_file)
        expected_tree = "(Coracias_caudata, (Gallus_gallus, Apus_affinis), (Acanthisitta_chloris, ((Formicarius_colma, Thamnophilus_nigrocinereus, Furnarius_rufus), (Tyrannus_tyrannus, (Pipra_coronata, Rupicola_rupicola)), (Pitta_guajana, (Smithornis_rufolateralis, (Philepitta_castanea, Psarisomus_dalhousiae)))), (Menura_novaehollandiae, (Climacteris_picumnus, Ptilonorhynchus_violaceus), (Aegithalos_iouschensis, Callaeas_cinerea, Notiomystis_cincta, Tregellasia_leucops, Troglodytes_aedon, Regulus_calendula, Sitta_pygmaea, Pycnonotus_barbatus, Picathartes_gymnocephalus, Parus_inornatus, Orthonyx_spaldingii, Petrochelidon_pyrrhonota, Cisticola_anonymus, Certhia_familiaris, Bombycilla_garrulus, Alauda_arvensis, (Ficedula_strophiata, Turdus_falklandii), (Meliphaga_analoga, Pardalotus_striatus), (Malurus_melanocephalus, Pomatostomus_isidorei), (Dicaeum_melanoxanthum, Nectarinia_olivacea), (Toxorhamphus_novaeguineae, (Melanocharis_nigra, Oedistoma_iliolophum)), (Sylvia_nana, (Garrulax_milleti, Zosterops_senegalensis)), (Cinclus_cinclus, (Mimus_patagonicus, Sturnus_vulgaris)), (Chloropsis_cochinchinensis, Irena_cyanogaster, (Cardinalis_cardinalis, Passer_montanus, Fringilla_montifringilla, (Motacilla_cinerea, Ploceus_cucullatus, Prunella_collaris), (Emberiza_schoeniclus, Thraupis_cyanocephala, Parula_americana, Icterus_parisorum))), ((Artamus_leucorynchus, (Aegithina_tiphia, Vanga_curvirostris)), ((Oriolus_larvatus, (Pachycephala_soror, Vireo_philadelphicus)), (Corvus_corone, Paradisaea_raggiana, (Monarcha_axillaris, Dicrurus_adsimilis), (Coracina_lineata, Lanius_ludovicianus))))))));" 
        self.assert_(trees_equal(expected_tree,tree))



    # combined tree after some processing
    def test_import_combined(self):
        test_file = "data/input/processed_tree.tre"
        tree = import_tree(test_file)
        expected_tree = "(Mimodes_graysoni, (Mimus_gilvus, Mimus_polyglottos), ((Mimus_gundlachii, (Nesomimus_macdonaldi, Nesomimus_melanotis, Nesomimus_parvulus, Nesomimus_trifasciatus)), ((Mimus_longicaudatus, ((Mimus_patagonicus, Mimus_thenca), (Mimus_saturninus, Mimus_triurus))), (Oreoscoptes_montanus, (Toxostoma_curvirostre, Toxostoma_rufum)))));" 
        self.assert_(trees_equal(expected_tree,tree))
        test_file = "data/input/processed_tree_translate.tre"
        tree = import_tree(test_file)
        expected_tree = "(Cettia_fortipes, ((((Garrulax_squamatus, Minla_ignotincta), ((Stachyris_chrysaea, Stachyris_ruficeps), Stachyris_nigriceps)), (((((Stachyris_whiteheadi, ((Zosterops_erythropleurus, Zosterops_japonicus), Zosterops_palpebrosus)), ((Yuhina_bakeri, Yuhina_flavicollis), (Yuhina_gularis, Yuhina_occipitalis))), (Yuhina_castaniceps, Yuhina_everetti)), (Yuhina_brunneiceps, Yuhina_nigrimenta)), Yuhina_diademata)), Yuhina_zantholeuca));"
        self.assert_(trees_equal(expected_tree,tree))



    def test_import_trees(self):
        """ Test reading all trees from a file """
        test_file = "data/input/multiple_trees.tre"
        tree = import_tree(test_file,tree_no=0)
        expected_tree = "(Coracias_caudata, (Gallus_gallus, Apus_affinis), (Acanthisitta_chloris, ((Formicarius_colma, Thamnophilus_nigrocinereus, Furnarius_rufus), (Tyrannus_tyrannus, (Pipra_coronata, Rupicola_rupicola)), (Pitta_guajana, (Smithornis_rufolateralis, (Philepitta_castanea, Psarisomus_dalhousiae)))), (Menura_novaehollandiae, (Climacteris_picumnus, Ptilonorhynchus_violaceus), (Aegithalos_iouschensis, Callaeas_cinerea, Notiomystis_cincta, Tregellasia_leucops, Troglodytes_aedon, Regulus_calendula, Sitta_pygmaea, Pycnonotus_barbatus, Picathartes_gymnocephalus, Parus_inornatus, Orthonyx_spaldingii, Petrochelidon_pyrrhonota, Cisticola_anonymus, Certhia_familiaris, Bombycilla_garrulus, Alauda_arvensis, (Ficedula_strophiata, Turdus_falklandii), (Meliphaga_analoga, Pardalotus_striatus), (Malurus_melanocephalus, Pomatostomus_isidorei), (Dicaeum_melanoxanthum, Nectarinia_olivacea), (Toxorhamphus_novaeguineae, (Melanocharis_nigra, Oedistoma_iliolophum)), (Sylvia_nana, (Garrulax_milleti, Zosterops_senegalensis)), (Cinclus_cinclus, (Mimus_patagonicus, Sturnus_vulgaris)), (Chloropsis_cochinchinensis, Irena_cyanogaster, (Cardinalis_cardinalis, Passer_montanus, Fringilla_montifringilla, (Motacilla_cinerea, Ploceus_cucullatus, Prunella_collaris), (Emberiza_schoeniclus, Thraupis_cyanocephala, Parula_americana, Icterus_parisorum))), ((Artamus_leucorynchus, (Aegithina_tiphia, Vanga_curvirostris)), ((Oriolus_larvatus, (Pachycephala_soror, Vireo_philadelphicus)), (Corvus_corone, Paradisaea_raggiana, (Monarcha_axillaris, Dicrurus_adsimilis), (Coracina_lineata, Lanius_ludovicianus))))))));" 
        self.assert_(trees_equal(expected_tree,tree))
        tree = import_tree(test_file, tree_no=1)
        expected_tree2 = "(Coracias_caudata, Gallus_gallus, Apus_affinis, (Acanthisitta_chloris, ((Formicarius_colma, Thamnophilus_nigrocinereus, Furnarius_rufus), (Tyrannus_tyrannus, (Pipra_coronata, Rupicola_rupicola)), (Pitta_guajana, (Smithornis_rufolateralis, (Philepitta_castanea, Psarisomus_dalhousiae)))), (Menura_novaehollandiae, (Climacteris_picumnus, Ptilonorhynchus_violaceus), (Aegithalos_iouschensis, Callaeas_cinerea, Notiomystis_cincta, Tregellasia_leucops, Troglodytes_aedon, Regulus_calendula, Sitta_pygmaea, Pycnonotus_barbatus, Picathartes_gymnocephalus, Parus_inornatus, Orthonyx_spaldingii, Petrochelidon_pyrrhonota, Cisticola_anonymus, Certhia_familiaris, Bombycilla_garrulus, Alauda_arvensis, (Ficedula_strophiata, Turdus_falklandii), (Meliphaga_analoga, Pardalotus_striatus), (Malurus_melanocephalus, Pomatostomus_isidorei), (Dicaeum_melanoxanthum, Nectarinia_olivacea), (Toxorhamphus_novaeguineae, (Melanocharis_nigra, Oedistoma_iliolophum)), (Sylvia_nana, (Garrulax_milleti, Zosterops_senegalensis)), (Cinclus_cinclus, (Mimus_patagonicus, Sturnus_vulgaris)), (Chloropsis_cochinchinensis, Irena_cyanogaster, (Cardinalis_cardinalis, Passer_montanus, Fringilla_montifringilla, (Motacilla_cinerea, Ploceus_cucullatus, Prunella_collaris), (Emberiza_schoeniclus, Thraupis_cyanocephala, Parula_americana, Icterus_parisorum))), ((Artamus_leucorynchus, (Aegithina_tiphia, Vanga_curvirostris)), ((Oriolus_larvatus, (Pachycephala_soror, Vireo_philadelphicus)), (Corvus_corone, Paradisaea_raggiana, (Monarcha_axillaris, Dicrurus_adsimilis), (Coracina_lineata, Lanius_ludovicianus))))))));" 
        self.assert_(trees_equal(expected_tree2,tree))
        trees = import_trees(test_file)
        self.assert_(trees_equal(expected_tree,trees[0]))        
        self.assert_(trees_equal(expected_tree2,trees[1]))


# test subbing and general messing with trees
class TestTreeManipulation(unittest.TestCase): 
    

    def test_unquoted_taxa_parse(self):
        tree="""(Lithobius_obscurus, Lithobius_variegatus, Australobius_scabrior, Bothropolys_multidentatus, ((Shikokuobius_japonicus, (Dichelobius_flavens, (Anopsobius_sp._nov._TAS, (Anopsobius_neozelanicus, Anopsobius_sp._nov._NSW)))), (Zygethobius_pontis, Cermatobius_japonicus), (Lamyctes_emarginatus, Lamyctes_africanus, Lamyctes_caeculus, Analamyctes_tucumanus, Analamyctes_andinus, (Lamyctopristus_validus, Lamyctopristus_sinuatus), (Easonobius_humilis, Easonobius_tridentatus, (Henicops_dentatus, (Henicops_maculatus, Henicops_sp._nov._QLD)))), (Paralamyctes_spenceri, Paralamyctes_neverneverensis, (Paralamyctes_asperulus, Paralamyctes_weberi), (Paralamyctes_tridens, (Paralamyctes_monteithi, Paralamyctes_harrisi)), (Paralamyctes_chilensis, (Paralamyctes_cassisi, Paralamyctes_mesibovi)), (Paralamyctes_validus, (Paralamyctes_grayi, 'Paralamyctes ?grayi', Paralamyctes_hornerae)), (Paralamyctes_subicolus, (Paralamyctes_trailli, (Paralamyctes_cammooensis, Paralamyctes_ginini))))));"""
        self.assert_(tree_contains("Paralamyctes_validus",tree))

    def test_assemble_tree_matrix(self):
        input_tree = '((A,B),F,E,(G,H));'
        matrix, taxa = assemble_tree_matrix(input_tree)
        # this should give us:
        expected_matrix = numpy.array(
                          [[1, 1, 0],
                           [1, 1, 0],
                           [1, 0, 0], 
                           [1, 0, 0], 
                           [1, 0, 1],
                           [1, 0, 1]])
        expected_taxa = ['A','B','F','E','G','H']
        self.assert_(matrix.all() == expected_matrix.all())
        self.assert_(expected_taxa == taxa)

        input_tree = '(A,B,C,D,E,F);'
        matrix, taxa = assemble_tree_matrix(input_tree)
        # this should give us:
        expected_matrix = numpy.array(
                          [[1],
                           [1],
                           [1], 
                           [1], 
                           [1],
                           [1]])
        expected_taxa = ['A','B','C','D','E','F']        
        self.assert_(matrix.all() == expected_matrix.all())
        self.assert_(expected_taxa == taxa)


    def test_delete_taxa(self):
        t = "((A_1,B_1),F_1,E_1,(G_1,H_1));"
        new_tree = delete_taxon("H_1", t)
        self.assert_(new_tree == "((A_1, B_1), F_1, E_1, G_1);")

    def test_delete_taxa_root(self):
        t = '((E%1,G%1),A,(G%2,(E%2,F,D,H,E%3)));'
        new_tree =  delete_taxon("E%1", t)
        new_tree =  delete_taxon("G%1", new_tree)
        new_tree =  delete_taxon("E%2", new_tree)
        self.assert_(new_tree == "(A, (G%2, (F, D, H, E%3)));")


    def test_delete_taxa_missing(self):
        t = "((A_1:1.00000,B_1:1.00000)0.00000:0.00000,F_1:1.00000,E_1:1.00000,(G_1:1.00000,H_1:1.00000)0.00000:0.00000)0.00000:0.00000;"
        new_tree = delete_taxon("Fred", t)
        self.assert_(trees_equal(new_tree, "((A_1,B_1),F_1,E_1,(G_1,H_1));"))

    def test_sub_taxa(self):
        t = "((A_1:1.00000,B_1:1.00000)0.00000:0.00000,F_1:1.00000,E_1:1.00000,(G_1:1.00000,H_1:1.00000)0.00000:0.00000)0.00000:0.00000;"
        new_tree = sub_taxon("H_1", "blah", t)
        self.assert_(trees_equal(new_tree, "((A_1,B_1),F_1,E_1,(G_1,blah));"))

    def test_sub_taxa_missing(self):
        t = "((A_1:1.00000,B_1:1.00000)0.00000:0.00000,F_1:1.00000,E_1:1.00000,(G_1:1.00000,H_1:1.00000)0.00000:0.00000)0.00000:0.00000;"
        new_tree = sub_taxon("Fred", "Blah",  t)
        self.assert_(trees_equal(new_tree, "((A_1,B_1),F_1,E_1,(G_1,H_1));"))

    def test_trees_equal(self):
        test_file = "data/input/multiple_trees.tre"
        trees = import_trees(test_file)
        self.assert_(trees_equal(trees[0],trees[0])==True)
        self.assert_(trees_equal(trees[1],trees[1])==True)

    def test_trees_not_equal(self):
        test_file = "data/input/multiple_trees.tre"
        trees = import_trees(test_file)
        self.assert_(trees_equal(trees[1],trees[0])==False)

    def test_trees_equal2(self):
        test_file = "data/input/equal_trees.new"
        trees = import_trees(test_file)
        self.assert_(trees_equal(trees[1],trees[0])==True)
        self.assert_(trees_equal(trees[3],trees[2])==False)


    def test_collapse_with_quotes(self):
        tree = "(Proteroiulus_fuscus, (Craterostigmus_tasmanianus, ((Scolopendra_viridis,(Lithobius_variegatus, (Paralamyctes_validus, Anopsobius_neozelanicus))),(Sphendononema_guildingii, ((Scutigerina_weberi%1, (Scutigerina_weberi%2,(Scutigerina_malagassa, Scutigerina_hova))), (Scutigera_coleoptrata,((Thereuopoda_longicornis, 'Thereuopodina, sp. nov.', (Thereuonema_tuberculata,Thereuonema_turkestana, Thereuopoda_clunifera)), (Allothereua_bidenticulata,Allothereua_serrulata, Parascutigera_festiva, Parascutigera_latericia))))))));"
        output = permute_tree(tree,treefile="newick")
        expected_tree = "(Proteroiulus_fuscus, (Craterostigmus_tasmanianus,((Scolopendra_viridis,(Lithobius_variegatus,(Paralamyctes_validus,Anopsobius_neozelanicus))),(Sphendononema_guildingii,((Scutigerina_weberi,(Scutigerina_malagassa, Scutigerina_hova)), (Scutigera_coleoptrata,((Thereuopoda_longicornis, 'Thereuopodina, sp. nov.', (Thereuonema_tuberculata,Thereuonema_turkestana, Thereuopoda_clunifera)), (Allothereua_bidenticulata,Allothereua_serrulata, Parascutigera_festiva, Parascutigera_latericia))))))));"
        self.assert_(trees_equal(output,expected_tree))


    def test_permute_tree_quoted(self):
        """Test an awkward tree to permute"""
        tree = "(((Theatops_posticus, (Cryptops_spinipes, Scolopocryptops_sexspinosus)),((Rhysida_nuda, ((Alipes_crotalus, (Ethmostigmus_rubripes, (Ethmostigmus_sp1, Ethmostigmus_sp2))), (((Rhysida_sp, (Rhysida_lithobiodis, Rhysida_imarginata%1)), (Rhysida_imarginata%2, Rhysida_longipes%1)), (Rhysida_imarginata%3, (Rhysida_imarginata%4, (Rhysida_imarginata%5, Rhysida_longipes%2)))), (Digitipes_coonoorensis, Digitipes_sp1, Digitipes_barnabasi, Digitipes_sp2))), ((Cormocephalus_monthanii, (Cormocephalus_nigrificatus, (Cormocephalus_sp1, (Cormocephalus_nudipes, (Cormocephalus_sp2, Cormocephalus_westwoodi))))), (('Scolopendra cf. morsitans%1', 'Scolopendra cf. morsitans%2', ('Scolopendra cf. morsitans%3', Scolopendra_cf._amazonica)), (Asanada_agharkari, Asanada_brevicornis))))), (Craterostigmus_tasmanianus, Craterostigmus_crabilli), (Mecistocephalus_guildingii, ((Himantarium_gabrielis, Bothriogaster_signata), (Geophilus_electricus, (Strigamia_maritima, Pachymerium_ferrugineum)))));"
        try:
            trees = permute_tree(tree,treefile="nexus")
        except:
            self.assert_(False)
        # just check this runs and doesn't err

    def test_getTaxaFromNewick_quoted(self):
        tree = "((Bothropolys_multidentatus, Lithobius_obscurus, 'Lithobius variegatus rubriceps', Lithobius_forficatus, Australobius_scabrior, Eupolybothrus_fasciatus), (Shikokuobius_japonicus, (Dichelobius_flavens, Dichelobius_ACT, (Anopsobius_TAS, (Anopsobius_neozelanicus, Anopsobius_NSW))), (Zygethobius_pontis, Cermatobius_japonicus, (Henicops_brevilabiatus, Henicops_dentatus, Henicops_SEQLD, (Lamyctes_emarginatus, Lamyctes_coeculus, Lamyctes_inermipes, Lamyctes_africanus, Lamyctes_hellyeri), (Henicops_maculatus_TAS, (Henicops_maculatus_NSW, Henicops_maculatus_NZ))), ('Paralamyctes (Paralamyctes) spenceri', 'Paralamyctes (Paralamyctes) weberi', 'Paralamyctes (Paralamyctes) asperulus', 'Paralamyctes (Paralamyctes) prendinii', 'Paralamyctes (Paralamyctes) tridens', 'Paralamyctes (Paralamyctes) neverneverensis', 'Paralamyctes (Paralamyctes) harrisi', 'Paralamyctes (Paralamyctes) monteithi SEQLD', 'Paralamyctes (Paralamyctes) monteithi NEQLD', 'Paralamyctes (Paralamyctes) monteithi MEQLD', ('Paralamyctes (Haasiella) trailli', 'Paralamyctes (Haasiella) subicolus'), ('Paralamyctes chilensis', 'Paralamyctes wellingtonensis'), ('Paralamyctes (Nothofagobius) cassisi', 'Paralamyctes (Nothofagobius) mesibovi'), ('Paralamyctes (Thingathinga) ?grayi', ('Paralamyctes (Thingathinga) grayi NSW1', 'Paralamyctes (Thingathinga) grayi NSW2')), ('Paralamyctes (Thingathinga) validus NZ3', ('Paralamyctes (Thingathinga) validus NZ1', 'Paralamyctes (Thingathinga) validus NZ2'))))));"
        taxa = getTaxa(tree)
        self.assert_("Lithobius_variegatus_rubriceps" in taxa)


if __name__ == '__main__':
    unittest.main()
 
