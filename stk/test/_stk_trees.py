import unittest
import sys
# so we import local stk before any other
sys.path.insert(0,"../../")
from stk.stk_trees import import_tree, import_trees, trees_equal, tree_contains, assemble_tree_matrix
from stk.stk_trees import delete_taxon, sub_taxon, permute_tree, get_taxa, collapse_nodes
from stk.stk_trees import get_all_siblings, read_matrix, parse_tree, parse_trees, sub_taxa_in_tree
from stk.stk_trees import correctly_quote_taxa, remove_single_poly_taxa
import numpy
import os
from lxml import etree
import tempfile
import stk.p4 as p4
# our test dataset
import tempfile
import stk.stk_exceptions as excp
import stk.stk_phyml as stk_phyml

standard_tre = "data/input/test_tree.tre"
single_source_input = "data/input/single_source.phyml"
expected_tree = '((Taxon_c:1.00000,(Taxon_a:1.00000,Taxon_b:1.00000)0.00000:0.00000)0.00000:0.00000,(Taxon_d:1.00000,Taxon_e:1.00000)0.00000:0.00000)0.00000:0.00000;'
parser = etree.XMLParser(remove_blank_text=True)

# To run a single test:
# python -m unittest _trees.TestImportTree.test_permute_trees

# Test the loading and saving of trees files in various forms
class TestImportExportTree(unittest.TestCase):

    def test_parse_tree(self):
        tree = expected_tree
        try:
            t = parse_tree(tree)
            self.assert_(True)
        except excp.TreeParseError:
            self.assert_(False)

    
    def test_parse_tree_fail(self):
        tree = "dvqwvwvefvfevfevefv34f!@JNn21@"
        try:
            t = parse_tree(tree)
            self.assert_(False)
        except excp.TreeParseError:
            self.assert_(True)

    def test_parse_treess(self):
        tree = expected_tree
        try:
            t = parse_trees(tree)
            self.assert_(True)
        except excp.TreeParseError:
            self.assert_(False)

    
    def test_parse_trees_fail(self):
        tree = "dvqwvwvefvfevfevefv34f!@JNn21@"
        try:
            t = parse_trees(tree)
            self.assert_(False)
        except excp.TreeParseError:
            self.assert_(True)


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

    def testtrees_equal(self):
        test_file = "data/input/multiple_trees.tre"
        trees = import_trees(test_file)
        self.assert_(trees_equal(trees[0],trees[0])==True)
        self.assert_(trees_equal(trees[1],trees[1])==True)

    def test_trees_not_equal(self):
        test_file = "data/input/multiple_trees.tre"
        trees = import_trees(test_file)
        self.assert_(trees_equal(trees[1],trees[0])==False)

    def testtrees_equal2(self):
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
        taxa = get_taxa(tree)
        self.assert_("Lithobius_variegatus_rubriceps" in taxa)

    def test_collapse_nodes(self):
        in_tree = "(taxa_a, (taxa_b, taxa_c), taxa_d, (taxa_e, taxa_h%3, (taxa_f, (taxa_g, taxa_h%1, taxa_h%2))));"
        answer = "(taxa_a, (taxa_b, taxa_c), taxa_d, (taxa_e, taxa_h%1, (taxa_f, (taxa_g, taxa_h%2))));"
        new_tree = collapse_nodes(in_tree);
        self.assert_(trees_equal(new_tree, answer), "Correctly collapse nodes")


    def test_delete_percent_taxa(self):
        tree = "(A%3, B, (C, D), E, F, G, (A%1, A%2));"
        new_tree = sub_taxa_in_tree(tree,"A")
        expected_tree = "(B, (C, D), E, F, G);"
        self.assert_(trees_equal(expected_tree,new_tree))

    def test_delete_and_collapse(self):
        tree = "(A%3, B, (C, D), E, F, G, (A%1, A%2));"
        new_tree = sub_taxa_in_tree(tree,"B")
        expected_tree = "(A%1, (C, D), E, F, G, A%2);"
        self.assert_(trees_equal(expected_tree,new_tree))


    def old_stk_replace_taxa_tests(self):
        original_trees = "((((Catharacta_maccormicki,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus);";
        tree1 = "((((replaced_taxon,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus);"
        tree2 = "((((Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus);"
        tree3 = "((((taxon_1,taxon_2,taxon_3,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus);"

        polytomy = "taxon_1,taxon_2,taxon_3"
        polytomy2 = "Skua_blah,Parasiticus_oops"
        polytomy3 = "Catharacta_chilensis,replaced_taxon"
        new_tree = sub_taxa_in_tree(original_trees,'Catharacta_maccormicki','replaced_taxon')
        self.assert_(trees_equal(new_tree,tree1))
        
        new_tree = sub_taxa_in_tree(original_trees,'Catharacta_maccormicki')
        self.assert_(trees_equal(new_tree,tree2), "Correctly deleted taxon")

        new_tree = sub_taxa_in_tree(original_trees,'Catharacta_maccormicki',polytomy)
        self.assert_(trees_equal(new_tree,tree3),"Correctly replaced with polytomy");

        new_tree = sub_taxa_in_tree(original_trees,'Catharacta maccormicki')
        self.assert_(trees_equal(new_tree, tree2), "Correctly deleted taxon with space in name");

        new_tree = sub_taxa_in_tree(original_trees,'Catharacta_Maccormicki');
        self.assert_((not trees_equal(new_tree, tree2)), "Didn't delete taxon with incorrect case");
        self.assert_(trees_equal(new_tree, original_trees), "Didn't delete taxon with incorrect case");

        new_tree = sub_taxa_in_tree(original_trees,'Catharacta maccormicki','replaced_taxon');
        self.assert_(trees_equal(new_tree, tree1), "Correctly replaced taxon with spaces in name");

        new_tree = sub_taxa_in_tree(original_trees,'Catharacta_Maccormicki',polytomy);
        self.assert_((not trees_equal(new_tree, tree3)), "Didn't replace taxon with incorrect case");
        self.assert_(trees_equal(new_tree, original_trees), "Didn't replace taxon with incorrect case");

        # check for partial replacement which we don't want
        new_tree = sub_taxa_in_tree(original_trees,'skua',polytomy2)
        self.assert_(trees_equal(new_tree, original_trees), "Correctly skipped partial match")

        # checking for adding duplicate taxa
        new_tree = sub_taxa_in_tree(original_trees,'Catharacta_maccormicki',polytomy3)
        self.assert_(trees_equal(new_tree, tree1), "Correctly substituted but no duplicates with polytomy");

        new_tree = sub_taxa_in_tree(original_trees,"Catharacta_maccormicki",'Catharacta_chilensis')
        self.assert_(trees_equal(new_tree, tree2), "Correctly substituted but no duplicates with single")


    def test_sub_quoted_taxa(self):

        quote_taxa_tree = "(taxa_1, 'taxa_n=taxa_2', taxa_3, taxa_4);";
        original_trees = "((((Catharacta_maccormicki,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus);";
        polytomy4 = "taxon_1,taxon_1,taxon_2,taxon_3"
        tree3 = "(((((taxon_1,taxon_2,taxon_3),Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus);"
        
        # checking for correct subbing of quoted taxa
        new_tree = sub_taxa_in_tree(quote_taxa_tree,"'taxa_n=taxa_2'",'taxa_2')
        self.assert_(trees_equal(new_tree,"(taxa_1,taxa_2,taxa_3,taxa_4);"),"Correctly substituted quoted taxa") 

        # quoted with + in it
        new_tree = sub_taxa_in_tree("(taxa_1, 'taxa_n+taxa_2', taxa_3, taxa_4);","'taxa_n+taxa_2'",'taxa_2');
        self.assert_(trees_equal(new_tree,"(taxa_1,taxa_2,taxa_3,taxa_4);"),"Correctly substituted quoted taxa") 

        # don't sub partial match of quoted taxa
        new_tree = sub_taxa_in_tree(quote_taxa_tree,"taxa_2",'taxa_8');
        answer = "(taxa_1,'taxa_n=taxa_2',taxa_3,taxa_4);"
        self.assert_(trees_equal(new_tree, answer), "Didn't substitute part of quoted taxa")

        # don't sub in repeated taxa
        new_tree = sub_taxa_in_tree(original_trees,'Catharacta_maccormicki',polytomy4)
        self.assert_(trees_equal(new_tree, tree3), "Didn't add repeated names");

        # checking removal of quoted taxa
        new_tree = sub_taxa_in_tree("(taxa_1, 'taxa_n+taxa_2', taxa_3, taxa_4);","'taxa_n+taxa_2'");
        self.assert_(trees_equal(new_tree, "(taxa_1,taxa_3,taxa_4);"), "Dealt with quoted taxa");

        new_tree = sub_taxa_in_tree("(taxa_1, 'taxa_n+taxa_2', 'taxa_3=taxa5', taxa_4);","'taxa_3=taxa5'");
        self.assert_(trees_equal(new_tree, "(taxa_1,'taxa_n+taxa_2',taxa_4);"), "Dealt with double quoted tacxa");

        polytomy5 = "taxon_n,'taxon_n+taxon_2',taxon_2,taxon_3"
        tree_in = "(taxa_n, 'taxa_n+taxa_2', 'taxa_3=taxa5', taxa_4);"
        new_tree = sub_taxa_in_tree(tree_in,"taxa_4", polytomy5)
        answer = "(taxa_n,'taxa_n+taxa_2','taxa_3=taxa5',(taxon_n,'taxon_n+taxon_2',taxon_2,taxon_3));"
        self.assert_(trees_equal(new_tree, answer), "Dealt with double quoted taxa");


    def test_sub_bug_fixes(self):
        tree4 = "(Apsaravis,Hesperornis,Ichthyornis,(Vegavis_iaai,(('Cathartidae=Ciconiidae',Modern_birds),('Recurvirostridae=Charadriidae',Protopteryx_fengningensis))));";
        tree4_result = "(Apsaravis,Hesperornis,Ichthyornis,(Vegavis_iaai,(('Cathartidae=Ciconiidae',Modern_birds%1),(Modern_birds%2,Protopteryx_fengningensis))));"
        original_trees = "((((Catharacta_maccormicki,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus);"

        # This is a different result to the old STK, but is actualy correct - you're replacing
        # in a non-monophyletic group.
        new_tree = sub_taxa_in_tree(tree4,"'Recurvirostridae=Charadriidae'",'Modern_birds');
        self.assert_(trees_equal(new_tree, tree4_result), "Correct replacement of taxa that already exists");

        ## New bug: replacing with the same taxa 
        new_tree = sub_taxa_in_tree(original_trees,"Catharacta_maccormicki",'Catharacta_maccormicki');
        self.assert_(trees_equal(new_tree,original_trees), "Correct ignored taxa replaced with itself");
    
    
    def test_collapse_tree(self):

        original_trees = "((((Catharacta_maccormicki,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus);"

        ## Trying out new function to collapse clades when going from specific to generic
        tree1 = "(((Catharacta%1,(Catharacta%2,Stercorarius%1)),Stercorarius%2),Larus);"
        new_tree = sub_taxa_in_tree(original_trees,"Catharacta_maccormicki",'Catharacta');
        new_tree = sub_taxa_in_tree(new_tree, "Catharacta_chilensis",'Catharacta');
        new_tree = sub_taxa_in_tree(new_tree, "Catharacta_antarctica",'Catharacta');
        new_tree = sub_taxa_in_tree(new_tree, "Catharacta_skua",'Catharacta');
        new_tree = sub_taxa_in_tree(new_tree, "Stercorarius_pomarinus",'Stercorarius');
        new_tree = sub_taxa_in_tree(new_tree, "Stercorarius_parasiticus",'Stercorarius');
        new_tree = sub_taxa_in_tree(new_tree, "Stercorarius_longicaudus",'Stercorarius');
        new_tree = sub_taxa_in_tree(new_tree, "Larus_argentatus",'Larus');
        self.assert_(trees_equal(new_tree, tree1), "Correctly collapse tree")


        hard_tree = "(Daphnia,Drosophila,Euphausia,Exopheticus,Petrolisthes,Pinnotherelia,Tritodynamia,(Ligia,(Armadillidium,Eocarcinus,Metapenaeus,((((((Himalayapotamon,Jasus,Polycheles,(Enoplometopus,((Pemphix,(((Thaumastocheles,(Acanthacaris,Enoplometopus1,Eryma,Homarus,Metanephrops,Nephropides,Nephrops,Nephropsis,Thaumastocheles1,Thaumastochelopsis,((Euastacus,(Astacoides,Geocharax,(Paranephrops,(Astacopsis,(Ombrastacoides,(Gramastacus,Cherax))))),(Parastacus,(Samastacus,Virilastacus))))))))))))))))))));";
        answer = "(Daphnia,Drosophila,Euphausia,Exopheticus,Petrolisthes,Pinnotherelia,Tritodynamia,(Ligia,(Armadillidium,Eocarcinus,Metapenaeus,(Himalayapotamon,Jasus,Polycheles,(Enoplometopus,(Pemphix,(Thaumastocheles,(Acanthacaris,Enoplometopus1,Eryma,Homarus,Metanephrops,Nephropides,Nephrops,Nephropsis,Thaumastocheles1,Thaumastochelopsis,(Euastacus,(Parastacidae%1,Geocharax,(Parastacidae%2,(Astacopsis,Parastacidae%3))),Parastacidae%4)))))))));";
        new_tree = sub_taxa_in_tree(hard_tree,"Astacoides",'Parastacidae');
        new_tree = sub_taxa_in_tree(new_tree,"Astacoides1",'Parastacidae');
        new_tree = sub_taxa_in_tree(new_tree,"Cherax",'Parastacidae');
        new_tree = sub_taxa_in_tree(new_tree,"Cherax1",'Parastacidae');
        new_tree = sub_taxa_in_tree(new_tree,"Gramastacus",'Parastacidae');
        new_tree = sub_taxa_in_tree(new_tree,"Ombrastacoides",'Parastacidae');
        new_tree = sub_taxa_in_tree(new_tree,"Paranephrops",'Parastacidae');
        new_tree = sub_taxa_in_tree(new_tree,"Parastacus",'Parastacidae');
        new_tree = sub_taxa_in_tree(new_tree,"Samastacus",'Parastacidae');
        new_tree = sub_taxa_in_tree(new_tree,"Virilastacus",'Parastacidae');
        self.assert_(trees_equal(new_tree, answer), "Correctly collapse tree")


        

    def test_specific_to_generic(self):
        """Checks the correct change of taxonomic level from specific to generic"""
        in_tree=import_tree("data/input/large_tree_snippet.tre")
        subs_old_taxa = ["Phylloscopus_trochilus", "Phylloscopus_brehmi", "Phylloscopus_canariensis", "Phylloscopus_collybita",
                         "Phylloscopus_sindianus", "Phylloscopus_fuligiventer", "Phylloscopus_fuscatus", "Phylloscopus_orientalis",
                         "Phylloscopus_bonelli", "Phylloscopus_sibilatrix", "Phylloscopus_yunnanensis", "Phylloscopus_subviridis", 
                         "Phylloscopus_chloronotus", "Phylloscopus_proregulus", "Phylloscopus_humei", "Phylloscopus_inornatus", 
                         "Phylloscopus_maculipennis", "Phylloscopus_pulcher", "Phylloscopus_trivirgatus", "Phylloscopus_sarasinorum", 
                         "Phylloscopus_amoenus", "Phylloscopus_poliocephalus", "Phylloscopus_presbytes","Phylloscopus_borealis",
                         "Phylloscopus_magnirostris","Phylloscopus_borealoides","Phylloscopus_tenellipes","Phylloscopus_emeiensis", 
                         "Phylloscopus_nitidus","Phylloscopus_plumbeitarsus","Phylloscopus_trochiloides","Phylloscopus_cebuensis", 
                         "Phylloscopus_coronatus","Phylloscopus_ijimae","Phylloscopus_ruficapillus","Phylloscopus_umbrovirens"]
        subs_new_taxa = ["Phylloscopus", "Phylloscopus", "Phylloscopus", "Phylloscopus",
                         "Phylloscopus", "Phylloscopus", "Phylloscopus", "Phylloscopus",
                         "Phylloscopus", "Phylloscopus", "Phylloscopus", "Phylloscopus",
                         "Phylloscopus", "Phylloscopus", "Phylloscopus", "Phylloscopus",
                         "Phylloscopus", "Phylloscopus", "Phylloscopus", "Phylloscopus",
                         "Phylloscopus", "Phylloscopus", "Phylloscopus", "Phylloscopus",
                         "Phylloscopus", "Phylloscopus", "Phylloscopus", "Phylloscopus",
                         "Phylloscopus", "Phylloscopus", "Phylloscopus", "Phylloscopus",
                         "Phylloscopus", "Phylloscopus", "Phylloscopus", "Phylloscopus"]
        new_tree = sub_taxa_in_tree(in_tree,subs_old_taxa,subs_new_taxa);
        # Fixes a random bug where Phylloscopus0 would appear, followed by Phylloscopus00 in subsequent subs
        self.assert_(new_tree.find("Phylloscopus0") == -1)


    def test_not_replace_partial(self):
        quote_taxa_tree = "(taxa_1, taxa_n_taxa_2, taxa_3, taxa_4);";
        new_tree = sub_taxa_in_tree(quote_taxa_tree,"taxa_2",'taxa_8');
        answer = "(taxa_1, taxa_n_taxa_2, taxa_3, taxa_4);"
        self.assert_(trees_equal(new_tree, answer), "Didn't substitute part of taxa")

    def test_replace_with_quotes(self):
        quote_taxa_tree = "(taxa_1, taxa_2, 'taxa_(blah)_foo', taxa_4);"
        new_tree = sub_taxa_in_tree(quote_taxa_tree,"taxa_2",'taxa_8');
        answer = "(taxa_1, taxa_8, 'taxa_(blah)_foo', taxa_4);"
        self.assert_(trees_equal(new_tree, answer), "Did a sub with quoted taxa")

    def test_replace_with_quoted(self):
        quote_taxa_tree = "(taxa_1, taxa_2, 'taxa_(blah)_foo', taxa_4);"
        new_tree = sub_taxa_in_tree(quote_taxa_tree,"taxa_(blah)_foo",'taxa_8');
        answer = "(taxa_1, taxa_2, taxa_8, taxa_4);"
        self.assert_(trees_equal(new_tree, answer), "Did a sub on quoted taxa")
    
    def test_replace_with_quoted(self):
        quote_taxa_tree = "(taxa_1, taxa_2, 'taxa_(blah)_foo', taxa_4);"
        new_tree = sub_taxa_in_tree(quote_taxa_tree,"taxa_(blah)_foo");
        answer = "(taxa_1, taxa_2, taxa_4);"
        self.assert_(trees_equal(new_tree, answer), "Deleted quoted taxa")

    def test_check_trees_with_quoted_subs(self):
        """Some datasets have quoted taxa with subs
        """
        tree = """(Proteroiulus_fuscus, (((Scolopendra_viridis, Craterostigmus_tasmanianus), (Lithobius_variegatus_rubriceps, (Anopsobius_neozelanicus, Paralamyctes_validus))), (Madagassophora_hova, Scutigerina_malagassa, Scutigerina_cf._weberi, Scutigerina_weberi, ((Dendrothereua_homa, Dendrothereua_nubila), (Parascutigera_nubila, (Ballonema_gracilipes, (((Sphendononema_rugosa, 'Sphendononema guildingii%1', 'Sphendononema guildingii%2'),  ('"Scutigera" nossibei', ('Scutigera coleoptrata%1', 'Scutigera coleoptrata%2', 'Scutigera coleoptrata%3'), (Thereuopodina_sp._nov, Tachythereua_sp., (Pilbarascutigera_incola,  (Seychellonema_gerlachi, (Thereuopoda_longicornis, Thereuopoda_clunifera)))))), ((Thereuonema_turkestana, Thereuonema_tuberculata), (Parascutigera_cf._sphinx,Parascutigera_latericia, Parascutigera_festiva, Allothereua_serrulata, Allothereua_bidenticulata, Allothereua_linderi, ('Allothereua maculata%1', Allothereua_maculata%2), (Parascutigera_sp._QLD_3, Parascutigera_sp._QLD_2, Parascutigera_sp._QLD_1, Parascutigera_guttata))))))))));"""
        tree2 = """(Proteroiulus_fuscus, (((Scolopendra_viridis, Craterostigmus_tasmanianus), (Lithobius_variegatus_rubriceps, (Anopsobius_neozelanicus, Paralamyctes_validus))), (Madagassophora_hova, Scutigerina_malagassa, Scutigerina_cf._weberi, Scutigerina_weberi, ((Dendrothereua_homa, Dendrothereua_nubila), (Parascutigera_nubila, (Ballonema_gracilipes, (((Sphendononema_rugosa, Sphendononema_guildingii%1, Sphendononema_guildingii%2), ('"Scutigera" nossibei', (Scutigera_coleoptrata%1, Scutigera_coleoptrata%2, Scutigera_coleoptrata%3), (Thereuopodina_sp._nov, Tachythereua_sp., (Pilbarascutigera_incola, (Seychellonema_gerlachi, (Thereuopoda_longicornis, Thereuopoda_clunifera)))))), ((Thereuonema_turkestana, Thereuonema_tuberculata), (Parascutigera_cf._sphinx, Parascutigera_latericia, Parascutigera_festiva, Allothereua_serrulata, Allothereua_bidenticulata, Allothereua_linderi, (Allothereua_maculata%1, Allothereua_maculata%2), (Parascutigera_sp._QLD_3, Parascutigera_sp._QLD_2, Parascutigera_sp._QLD_1, Parascutigera_guttata))))))))));"""
        tree3 = """(Proteroiulus_fuscus, (((Scolopendra_viridis, Craterostigmus_tasmanianus), (Lithobius_variegatus_rubriceps, (Anopsobius_neozelanicus, Paralamyctes_validus))), (Madagassophora_hova, Scutigerina_malagassa, Scutigerina_cf._weberi, Scutigerina_weberi, ((Dendrothereua_homa, Dendrothereua_nubila), (Parascutigera_nubila, (Ballonema_gracilipes, (((Sphendononema_rugosa, Sphendononema_guildingii), ('"Scutigera" nossibei', Scutigera_coleoptrata, (Thereuopodina_sp._nov, Tachythereua_sp., (Pilbarascutigera_incola, (Seychellonema_gerlachi, (Thereuopoda_longicornis, Thereuopoda_clunifera)))))), ((Thereuonema_turkestana, Thereuonema_tuberculata), (Parascutigera_cf._sphinx, Parascutigera_latericia, Parascutigera_festiva, Allothereua_serrulata, Allothereua_bidenticulata, Allothereua_linderi, Allothereua_maculata, (Parascutigera_sp._QLD_3, Parascutigera_sp._QLD_2, Parascutigera_sp._QLD_1, Parascutigera_guttata))))))))));"""
        collapsed_tree =  correctly_quote_taxa(tree)
        self.assert_(trees_equal(tree2, collapsed_tree))
        collapsed_tree = collapse_nodes(collapsed_tree)
        collapsed_tree = remove_single_poly_taxa(collapsed_tree) 
        self.assert_(trees_equal(tree3, collapsed_tree))

class TestTreeFunctions(unittest.TestCase):

    
    def test_get_all_siblings(self):
        t = parse_tree("(A,B,C,D,E,F,G,H,I,J);")
        siblings = get_all_siblings(t.node(1))
        expected = ["B","C","D","E","F","G","H","I","J"]
        self.assertListEqual(siblings,expected)
        siblings = get_all_siblings(t.node(3)) # selects C - so tests we get left siblings too
        expected = ["A","B","D","E","F","G","H","I","J"]
        self.assertListEqual(siblings,expected)


class TestMatrixMethods(unittest.TestCase):

    
    def test_read_matrix_nexus(self):
        matrix,taxa = read_matrix("data/input/matrix.nex")
        expected_taxa = ['MRPOutgroup','A','B','B_b','C','D','E','F']
        expected_matrix = [
                            ["0","0","0","0","0","0"],
                            ["1","0","1","0","1","0"],
                            ["1","0","?","?","1","0"],
                            ["?","?","1","0","?","?"],
                            ["0","1","0","1","?","?"],
                            ["0","1","0","1","?","?"],
                            ["?","?","?","?","0","1"],
                            ["?","?","?","?","0","1"]
                          ]
        self.assertListEqual(expected_taxa,taxa)
        self.assertListEqual(expected_matrix,matrix)

    def test_read_matrix_tnt(self):
        matrix,taxa = read_matrix("data/input/matrix.tnt")
        expected_taxa = ['MRPOutgroup','A','B','B_b','C','D','E','F']
        expected_matrix = [
                            ["0","0","0","0","0","0"],
                            ["1","0","1","0","1","0"],
                            ["1","0","?","?","1","0"],
                            ["?","?","1","0","?","?"],
                            ["0","1","0","1","?","?"],
                            ["0","1","0","1","?","?"],
                            ["?","?","?","?","0","1"],
                            ["?","?","?","?","0","1"]
                          ]
        self.assertListEqual(expected_taxa,taxa)
        self.assertListEqual(expected_matrix,matrix)

    def test_read_matrix_nexus_p4(self):
        matrix,taxa = read_matrix("data/input/matrix_p4.nex")
        expected_taxa = ['MRPOutgroup','A','B','B_b','C','D','E','F']
        expected_matrix = [
                            ["0","0","0","0","0","0"],
                            ["1","0","1","0","1","0"],
                            ["1","0","?","?","1","0"],
                            ["?","?","1","0","?","?"],
                            ["0","1","0","1","?","?"],
                            ["0","1","0","1","?","?"],
                            ["?","?","?","?","0","1"],
                            ["?","?","?","?","0","1"]
                          ]
        self.assertListEqual(expected_taxa,taxa)
        self.assertListEqual(expected_matrix,matrix)


    def test_permute_trees(self):
        XML = etree.tostring(etree.parse('data/input/permute_trees.phyml',parser),pretty_print=True)
        trees = stk_phyml.get_all_trees(XML)
        # contains quoted taxa too
        output = permute_tree(trees['Hill_2011_1'],treefile="newick")
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".new")
        f = open(temp_file,"w")
        f.write(output)
        f.close()
        output_trees = import_trees(temp_file)
        expected_trees = import_trees("data/output/permute_trees.nex")
        os.remove(temp_file)
        self.assert_(len(output_trees)==len(expected_trees))
        for i in range(0,len(output_trees)):
            self.assert_(trees_equal(output_trees[i],expected_trees[i]))


    def test_permute_trees_2(self):
        XML = etree.tostring(etree.parse('data/input/permute_trees.phyml',parser),pretty_print=True)
        trees = stk_phyml.get_all_trees(XML)
        output = permute_tree(trees['Davis_2011_1'],treefile="newick")
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".new")
        f = open(temp_file,"w")
        f.write(output)
        f.close()
        output_trees = import_trees(temp_file)
        expected_trees = import_trees("data/output/permute_trees_2.nex")
        os.remove(temp_file)
        self.assert_(len(output_trees)==len(expected_trees))
   

    def test_permute_trees_3(self):
        XML = etree.tostring(etree.parse('data/input/permute_trees.phyml',parser),pretty_print=True)
        trees = stk_phyml.get_all_trees(XML)
        # contains quoted taxa too
        output = permute_tree(trees['Hill_Davis_2011_2'],treefile="newick")
        self.assert_(trees_equal(output,"(A, (B, (C, D, E_E, F, G)));"))


    def test_delete_taxa_root(self):
        tree_1 = "((Artemia_salina),((Kempina_mikado,Lysiosquillina_maculata,Squilla_empusa),Anchistioides_antiguensis,Atyoida_bisulcata));"
        output = delete_taxon("Artemia_salina",tree_1)
        expected_tree = "((Kempina_mikado,Lysiosquillina_maculata,Squilla_empusa),Anchistioides_antiguensis,Atyoida_bisulcata);"
        self.assert_(trees_equal(output, expected_tree))





    def test_collapse_permute_tree(self):
        tree = "((Parapurcellia_silvicola, ((Austropurcellia_scoparia, Austropurcellia_forsteri), ((Pettalus_sp.%1, Pettalus_sp.%2), ((Purcellia_illustrans, Chileogovea_sp.), ((Neopurcellia_salmoni, Karripurcellia_harveyi), ((Aoraki_inerma, Aoraki_denticulata), (Rakaia_antipodiana, (Rakaia_stewartiensis, Rakaia_florensis)))))))), (((Stylocellus_lydekkeri, (Stylocellus_sp.%1, Stylocellus_sp.%2)), ((Stylocellus_sp.%3, Stylocellus_sp.%4), (Fangensis_insulanus, (Fangensis_spelaeus, Fangensis_cavernarum)))), (((Paramiopsalis_ramulosus, (Cyphophthalmus_sp., (Cyphophthalmus_gjorgjevici, Cyphophthalmus_duricorius))), ((Siro_valleorum, Siro_rubens), (Siro_acaroides, (Siro_kamiakensis, Siro_exilis)))), (Suzukielus_sauteri, (Parasiro_coiffaiti, ((Troglosiro_longifossa, Troglosiro_aelleni), (Metasiro_americanus, ((Huitaca_sp., (Neogovea_sp., Metagovea_sp.)), (Paragovia_sp.%1, (Paragovia_sp.%2, (Paragovia_sp.%3, Paragovia_sironoides)))))))))));"
        expected_tree = "((Parapurcellia_silvicola, ((Austropurcellia_scoparia, Austropurcellia_forsteri), (Pettalus_sp.%1, ((Purcellia_illustrans, Chileogovea_sp.), ((Neopurcellia_salmoni, Karripurcellia_harveyi), ((Aoraki_inerma, Aoraki_denticulata), (Rakaia_antipodiana, (Rakaia_stewartiensis, Rakaia_florensis)))))))), (((Stylocellus_lydekkeri, Stylocellus_sp.%1), (Stylocellus_sp.%3, (Fangensis_insulanus, (Fangensis_spelaeus, Fangensis_cavernarum)))), (((Paramiopsalis_ramulosus, (Cyphophthalmus_sp., (Cyphophthalmus_gjorgjevici, Cyphophthalmus_duricorius))), ((Siro_valleorum, Siro_rubens), (Siro_acaroides, (Siro_kamiakensis, Siro_exilis)))), (Suzukielus_sauteri, (Parasiro_coiffaiti, ((Troglosiro_longifossa, Troglosiro_aelleni), (Metasiro_americanus, ((Huitaca_sp., (Neogovea_sp., Metagovea_sp.)), (Paragovia_sp.%1, (Paragovia_sp.%2, (Paragovia_sp.%3, Paragovia_sironoides)))))))))));"
        new_tree = collapse_nodes(tree);
        self.assert_(trees_equal(expected_tree,new_tree)) 


    def test_tree_contains_odd(self):
        tree = """(Proteroiulus_fuscus, (((Scolopendra_viridis, Craterostigmus_tasmanianus),
        (Lithobius_variegatus_rubriceps, (Anopsobius_neozelanicus, Paralamyctes_validus))),
        (Madagassophora_hova, Scutigerina_malagassa, Scutigerina_cf._weberi, Scutigerina_weberi,
        ((Dendrothereua_homa, Dendrothereua_nubila), (Parascutigera_nubila, (Ballonema_gracilipes,
        (((Sphendononema_rugosa, 'Sphendononema guildingii%1', 'Sphendononema guildingii%2'),
        ('"Scutigera" nossibei', ('Scutigera coleoptrata%1', 'Scutigera coleoptrata%2', 'Scutigera coleoptrata%3'), (Thereuopodina_sp._nov, Tachythereua_sp., (Pilbarascutigera_incola,
        (Seychellonema_gerlachi, (Thereuopoda_longicornis, Thereuopoda_clunifera)))))),
        ((Thereuonema_turkestana, Thereuonema_tuberculata), (Parascutigera_cf._sphinx,
            Parascutigera_latericia, Parascutigera_festiva, Allothereua_serrulata,
            Allothereua_bidenticulata, Allothereua_linderi, ('Allothereua maculata%1',
                Allothereua_maculata%2), (Parascutigera_sp._QLD_3, Parascutigera_sp._QLD_2,
                    Parascutigera_sp._QLD_1, Parascutigera_guttata))))))))));"""
        self.assert_(tree_contains('"Scutigera"_nossibei',tree))


    def test_replace_poly_taxa(self):
        tree = "(A_a%1, A_b%1, (A_a%2, A_b%2, A_c, A_d));"
        new_tree = sub_taxa_in_tree(tree,"A_a", "A_f")
        expected_tree = "(A_f%1, A_b%1, (A_f%2, A_b%2, A_c, A_d));"
        self.assert_(trees_equal(expected_tree,new_tree))


    def test_remove_single_poly_taxa(self):
        """ Remove poly taxa where there's only one anyway """

        tree = """(Proteroiulus_fuscus, (((Scolopendra_viridis, Craterostigmus_tasmanianus), (Lithobius_variegatus_rubriceps, (Anopsobius_neozelanicus, Paralamyctes_validus))), (Madagassophora_hova, Scutigerina_malagassa%1, Scutigerina_cf._weberi, Scutigerina_weberi, ((Dendrothereua_homa, Dendrothereua_nubila), (Parascutigera_nubila, (Ballonema_gracilipes, (((Sphendononema_rugosa, Sphendononema_guildingii%1), ('"Scutigera" nossibei', Scutigerina_malagassa%2, Scutigera_coleoptrata%1, (Thereuopodina_sp._nov, Tachythereua_sp., (Pilbarascutigera_incola, (Seychellonema_gerlachi, (Thereuopoda_longicornis, Thereuopoda_clunifera)))))), ((Thereuonema_turkestana, Thereuonema_tuberculata), (Parascutigera_cf._sphinx, Parascutigera_latericia, Parascutigera_festiva, Allothereua_serrulata, Allothereua_bidenticulata, Allothereua_linderi, Allothereua_maculata%1, (Parascutigera_sp._QLD_3, Parascutigera_sp._QLD_2, Parascutigera_sp._QLD_1, Parascutigera_guttata))))))))));"""
        tree2 = """(Proteroiulus_fuscus, (((Scolopendra_viridis, Craterostigmus_tasmanianus), (Lithobius_variegatus_rubriceps, (Anopsobius_neozelanicus, Paralamyctes_validus))), (Madagassophora_hova, Scutigerina_malagassa%1, Scutigerina_cf._weberi, Scutigerina_weberi, ((Dendrothereua_homa, Dendrothereua_nubila), (Parascutigera_nubila, (Ballonema_gracilipes, (((Sphendononema_rugosa, Sphendononema_guildingii), ('"Scutigera" nossibei', Scutigerina_malagassa%2, Scutigera_coleoptrata, (Thereuopodina_sp._nov, Tachythereua_sp., (Pilbarascutigera_incola, (Seychellonema_gerlachi, (Thereuopoda_longicornis, Thereuopoda_clunifera)))))), ((Thereuonema_turkestana, Thereuonema_tuberculata), (Parascutigera_cf._sphinx, Parascutigera_latericia, Parascutigera_festiva, Allothereua_serrulata, Allothereua_bidenticulata, Allothereua_linderi, Allothereua_maculata, (Parascutigera_sp._QLD_3, Parascutigera_sp._QLD_2, Parascutigera_sp._QLD_1, Parascutigera_guttata))))))))));"""
        collapsed_tree = remove_single_poly_taxa(tree)
        self.assert_(trees_equal(tree2, collapsed_tree))


    def test_subspecies_sub(self):
        """ Checking the sub of sub species """

        tree1 = """(taxa_1, 'taxa 2', 'taxa (blah?) foo', bob);"""
        tree2 = """(taxa_1, taxa_2, taxa_8, bob);"""
        new_tree = sub_taxa_in_tree(tree1,"taxa_(blah?)_foo",'taxa_8');
        self.assert_(trees_equal(new_tree, tree2), "Did a sub on quoted odd taxon")
        tree1 = """(taxa_1, 'taxa 2', 'taxa blah?', bob);"""
        new_tree = sub_taxa_in_tree(tree1,"taxa_blah?",'taxa_8');
        self.assert_(trees_equal(new_tree, tree2), "Did a sub on quoted odd taxon")
        tree1 = """(taxa_1, 'taxa 2', 'taxa blah,sp2 nov', bob);"""
        new_tree = sub_taxa_in_tree(tree1,"taxa_blah,sp2_nov",'taxa_8');
        self.assert_(trees_equal(new_tree, tree2), "Did a sub on quoted odd taxon")

    def test_quoted_subin(self):
        """ sub in taxa that need quoting """
        tree1 = """(Thereuonema_turkestana, Thereuopodina, 'Thereuopodina, sp. nov.');"""
        answer1 = """(Thereuonema_turkestana, Thereuopodina_nov._sp., Thereuopodina_n._sp., Thereuopodina_queenslandica, Thereuopodina_sp._nov, 'Thereuopodina, sp. nov.')"""
        tree2 = """(Thereuonema_turkestana, Thereuopodina, Bob, Fred);"""
        answer2 = """(Thereuonema_turkestana, Thereuopodina_nov._sp., 'Thereuopodina,_sp._nov.', Thereuopodina_n._sp., Thereuopodina_queenslandica, Thereuopodina_sp._nov, Bob, Fred);"""
        sub_in = "'Thereuopodina,_sp._nov.','Thereuopodina_n._sp.','Thereuopodina_nov._sp.',Thereuopodina_queenslandica,'Thereuopodina_sp._nov'"
        new_tree = sub_taxa_in_tree(tree1,"Thereuopodina",sub_in,skip_existing=True);
        self.assert_(answer1, new_tree)
        new_tree = sub_taxa_in_tree(tree2,"Thereuopodina",sub_in,skip_existing=True);
        self.assert_(answer2, new_tree)



if __name__ == '__main__':
    unittest.main()
 
