#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 3;

use lib 'lib';
use Bio::STK;

my $dir = "t/data/test_data";
my @taxa = ("Afropavo congensis","Alectoris chukar","Alectoris rufa","Asthenes dorbignyi","Bambusicola thoracica","Cacomantis flabelliformis","Campylorhamphus falcularius","Campylorhamphus procurvoides","Campylorhamphus trochilirostris","Carduelis ambigua","Carduelis atrata","Carduelis barbata","Carduelis cannabina","Carduelis carduelis","Carduelis chloris","Carduelis crassirostris","Carduelis cucullata","Carduelis flammea","Carduelis flavirostris","Carduelis hornemanni","Carduelis lawrencei","Carduelis magellanica","Carduelis notata","Carduelis olivacea","Carduelis pinus","Carduelis psaltria","Carduelis sinica","Carduelis spinescens","Carduelis spinoides","Carduelis spinus","Carduelis tristis","Carduelis xanthogastra","Carduelis yarrellii","Catharacta antarctica","Catharacta chilensis","Catharacta hamiltoni","Catharacta lonnbergi","Catharacta maccormicki","Catharacta skua","Catreus wallichii","Cercococcyx montanus","Chondestes grammacus","Chrysococcyx osculans","Clamator glandarius","Clamator jacobinus","Crax pauxi","Crossoptilon crossoptilon","Cuculus canorus","Cuculus poliocephalus","Cyrtonyx montezumae","Dendrexetastes rufigula","Dendrocolaptes certhia","Dromococcyx phasianellus","Falcipennis canadensis","Fringilla coelebs","Gallus gallus","Geococcyx californianus","Glyphorynchus spirurus","Guira guira","Hylexetastes perrotii","Larus argentatus","Larus armenicus","Larus atlanticus","Larus atricilla","Larus audouinii","Larus belcheri","Larus brunnicephalus","Larus bulleri","Larus cachinnans","Larus californicus","Larus canus","Larus cirrocephalus","Larus crassirostris","Larus delawarensis","Larus dominicanus","Larus fuliginosus","Larus fuscus","Larus genei","Larus glaucescens","Larus glaucoides","Larus hartlaubii","Larus heermanni","Larus hemprichii","Larus heuglini","Larus hyperboreus","Larus ichthyaetus","Larus leucophthalmus","Larus livens","Larus maculipennis","Larus marinus","Larus melanocephalus","Larus michahellis","Larus minutus","Larus modestus","Larus novaehollandiae","Larus occidentalis","Larus pacificus","Larus philadelphia","Larus pipixcan","Larus relictus","Larus ridibundus","Larus saundersi","Larus schistisagus","Larus scopulinus","Larus scoresbii","Larus serranus","Larus taimyrensis","Larus thayeri","Lepidocolaptes albolineatus","Lepidocolaptes angustirostris","Lepidocolaptes fuscus","Lonchura cucullata","Lophura nycthemera","MRPoutgroup","Meleagris gallopavo","Miliaria calandra","Myornis senilis","Nasica longirostris","Neomorphus geoffroyi","Numida meleagris","Oreortyx pictus","Ortalis vetula","Passer ammodendri","Passer domesticus","Passer flaveolus","Passer griseus","Passer hispaniolensis","Passer luteus","Passer melanurus","Passer montanus","Passer rutilans","Pavo cristatus","Pavo muticus","Perdix perdix","Petronia petronia","Phaenicophaeus superciliosus","Piaya cayana","Pitta sordida","Pucrasia macrolopha","Quelea cardinalis","Scytalopus magellanicus","Scytalopus parvirostris","Scytalopus schulenbergi","Scytalopus simonsi","Serinus alario","Serinus albogularis","Serinus atrogularis","Serinus canaria","Serinus canicollis","Serinus citrinella","Serinus citrinelloides","Serinus citrinipectus","Serinus dorsostriatus","Serinus flaviventris","Serinus gularis","Serinus leucopygius","Serinus mozambicus","Serinus pusillus","Serinus serinus","Serinus striolatus","Serinus sulphuratus","Serinus thibetanus","Sittasomus griseicapillus","Spizella passerina","Stercorarius longicaudus","Stercorarius parasiticus","Stercorarius pomarinus","Surniculus lugubris","Tapera naevia","Tympanuchus phasianellus","Xiphocolaptes promeropirhynchus","Xiphorhynchus erythropygius","Xiphorhynchus flavigaster","Xiphorhynchus guttatus","Xiphorhynchus kienerii","Xiphorhynchus lachrymosus","Xiphorhynchus obsoletus","Xiphorhynchus ocellatus","Xiphorhynchus pardalotus","Xiphorhynchus picus","Xiphorhynchus spixii","Xiphorhynchus susurrans","Xiphorhynchus triangularis");
my @test_taxa = Bio::STK::get_taxa_list($dir);
is_deeply (\@test_taxa, \@taxa, "Correctly found all taxa");

#this test should die, so wrap it up...
eval {
    Bio::STK::get_taxa_list('t/data/test_data/nonsense.dat'); 
};
ok($@, 'Croaked correctly');
like($@, qr/Directory .* does not exist/, '... and it is the correct exception');
