"""master schools and cities

Revision ID: 20261114_8
Revises: 20261114_7
Create Date: 2026-11-14 00:00:00.000000

Deletes the 4 junk accounts flagged in the raw data review (MAN 1, SMA 101,
SMP1, Al Azhar schools), seeds the 514 Indonesian kabupaten/kota cities and
the canonical schools (see the alias tables), backfills school_id/city_id
FKs, then drops the free-text school/city/country columns.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import bindparam, text

revision: str = "20261114_8"
down_revision: str | None = "20261114_7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CITIES = (
    "Kabupaten Aceh Barat",
    "Kabupaten Aceh Barat Daya",
    "Kabupaten Aceh Besar",
    "Kabupaten Aceh Jaya",
    "Kabupaten Aceh Selatan",
    "Kabupaten Aceh Singkil",
    "Kabupaten Aceh Tamiang",
    "Kabupaten Aceh Tengah",
    "Kabupaten Aceh Tenggara",
    "Kabupaten Aceh Timur",
    "Kabupaten Aceh Utara",
    "Kabupaten Administrasi Kepulauan Seribu",
    "Kabupaten Agam",
    "Kabupaten Alor",
    "Kabupaten Asahan",
    "Kabupaten Asmat",
    "Kabupaten Badung",
    "Kabupaten Balangan",
    "Kabupaten Bandung",
    "Kabupaten Bandung Barat",
    "Kabupaten Banggai",
    "Kabupaten Banggai Kepulauan",
    "Kabupaten Banggai Laut",
    "Kabupaten Bangka",
    "Kabupaten Bangka Barat",
    "Kabupaten Bangka Selatan",
    "Kabupaten Bangka Tengah",
    "Kabupaten Bangkalan",
    "Kabupaten Bangli",
    "Kabupaten Banjar",
    "Kabupaten Banjarnegara",
    "Kabupaten Bantaeng",
    "Kabupaten Bantul",
    "Kabupaten Banyuasin",
    "Kabupaten Banyumas",
    "Kabupaten Banyuwangi",
    "Kabupaten Barito Kuala",
    "Kabupaten Barito Selatan",
    "Kabupaten Barito Timur",
    "Kabupaten Barito Utara",
    "Kabupaten Barru",
    "Kabupaten Batang",
    "Kabupaten Batanghari",
    "Kabupaten Batu Bara",
    "Kabupaten Bekasi",
    "Kabupaten Belitung",
    "Kabupaten Belitung Timur",
    "Kabupaten Belu",
    "Kabupaten Bener Meriah",
    "Kabupaten Bengkalis",
    "Kabupaten Bengkayang",
    "Kabupaten Bengkulu Selatan",
    "Kabupaten Bengkulu Tengah",
    "Kabupaten Bengkulu Utara",
    "Kabupaten Berau",
    "Kabupaten Biak Numfor",
    "Kabupaten Bima",
    "Kabupaten Bintan",
    "Kabupaten Bireuen",
    "Kabupaten Blitar",
    "Kabupaten Blora",
    "Kabupaten Boalemo",
    "Kabupaten Bogor",
    "Kabupaten Bojonegoro",
    "Kabupaten Bolaang Mongondow",
    "Kabupaten Bolaang Mongondow Selatan",
    "Kabupaten Bolaang Mongondow Timur",
    "Kabupaten Bolaang Mongondow Utara",
    "Kabupaten Bombana",
    "Kabupaten Bondowoso",
    "Kabupaten Bone",
    "Kabupaten Bone Bolango",
    "Kabupaten Boven Digoel",
    "Kabupaten Boyolali",
    "Kabupaten Brebes",
    "Kabupaten Buleleng",
    "Kabupaten Bulukumba",
    "Kabupaten Bulungan",
    "Kabupaten Bungo",
    "Kabupaten Buol",
    "Kabupaten Buru",
    "Kabupaten Buru Selatan",
    "Kabupaten Buton",
    "Kabupaten Buton Selatan",
    "Kabupaten Buton Tengah",
    "Kabupaten Buton Utara",
    "Kabupaten Ciamis",
    "Kabupaten Cianjur",
    "Kabupaten Cilacap",
    "Kabupaten Cirebon",
    "Kabupaten Dairi",
    "Kabupaten Deiyai",
    "Kabupaten Deli Serdang",
    "Kabupaten Demak",
    "Kabupaten Dharmasraya",
    "Kabupaten Dogiyai",
    "Kabupaten Dompu",
    "Kabupaten Donggala",
    "Kabupaten Empat Lawang",
    "Kabupaten Ende",
    "Kabupaten Enrekang",
    "Kabupaten Fakfak",
    "Kabupaten Flores Timur",
    "Kabupaten Garut",
    "Kabupaten Gayo Lues",
    "Kabupaten Gianyar",
    "Kabupaten Gorontalo",
    "Kabupaten Gorontalo Utara",
    "Kabupaten Gowa",
    "Kabupaten Gresik",
    "Kabupaten Grobogan",
    "Kabupaten Gunung Mas",
    "Kabupaten Gunungkidul",
    "Kabupaten Halmahera Barat",
    "Kabupaten Halmahera Selatan",
    "Kabupaten Halmahera Tengah",
    "Kabupaten Halmahera Timur",
    "Kabupaten Halmahera Utara",
    "Kabupaten Hulu Sungai Selatan",
    "Kabupaten Hulu Sungai Tengah",
    "Kabupaten Hulu Sungai Utara",
    "Kabupaten Humbang Hasundutan",
    "Kabupaten Indragiri Hilir",
    "Kabupaten Indragiri Hulu",
    "Kabupaten Indramayu",
    "Kabupaten Intan Jaya",
    "Kabupaten Jayapura",
    "Kabupaten Jayawijaya",
    "Kabupaten Jember",
    "Kabupaten Jembrana",
    "Kabupaten Jeneponto",
    "Kabupaten Jepara",
    "Kabupaten Jombang",
    "Kabupaten Kaimana",
    "Kabupaten Kampar",
    "Kabupaten Kapuas",
    "Kabupaten Kapuas Hulu",
    "Kabupaten Karanganyar",
    "Kabupaten Karangasem",
    "Kabupaten Karawang",
    "Kabupaten Karimun",
    "Kabupaten Karo",
    "Kabupaten Katingan",
    "Kabupaten Kaur",
    "Kabupaten Kayong Utara",
    "Kabupaten Kebumen",
    "Kabupaten Kediri",
    "Kabupaten Keerom",
    "Kabupaten Kendal",
    "Kabupaten Kepahiang",
    "Kabupaten Kepulauan Anambas",
    "Kabupaten Kepulauan Aru",
    "Kabupaten Kepulauan Mentawai",
    "Kabupaten Kepulauan Meranti",
    "Kabupaten Kepulauan Sangihe",
    "Kabupaten Kepulauan Selayar",
    "Kabupaten Kepulauan Siau Tagulandang Biaro",
    "Kabupaten Kepulauan Sula",
    "Kabupaten Kepulauan Talaud",
    "Kabupaten Kepulauan Tanimbar",
    "Kabupaten Kepulauan Yapen",
    "Kabupaten Kerinci",
    "Kabupaten Ketapang",
    "Kabupaten Klaten",
    "Kabupaten Klungkung",
    "Kabupaten Kolaka",
    "Kabupaten Kolaka Timur",
    "Kabupaten Kolaka Utara",
    "Kabupaten Konawe",
    "Kabupaten Konawe Kepulauan",
    "Kabupaten Konawe Selatan",
    "Kabupaten Konawe Utara",
    "Kabupaten Kotabaru",
    "Kabupaten Kotawaringin Barat",
    "Kabupaten Kotawaringin Timur",
    "Kabupaten Kuantan Singingi",
    "Kabupaten Kubu Raya",
    "Kabupaten Kudus",
    "Kabupaten Kulon Progo",
    "Kabupaten Kuningan",
    "Kabupaten Kupang",
    "Kabupaten Kutai Barat",
    "Kabupaten Kutai Kartanegara",
    "Kabupaten Kutai Timur",
    "Kabupaten Labuhanbatu",
    "Kabupaten Labuhanbatu Selatan",
    "Kabupaten Labuhanbatu Utara",
    "Kabupaten Lahat",
    "Kabupaten Lamandau",
    "Kabupaten Lamongan",
    "Kabupaten Lampung Barat",
    "Kabupaten Lampung Selatan",
    "Kabupaten Lampung Tengah",
    "Kabupaten Lampung Timur",
    "Kabupaten Lampung Utara",
    "Kabupaten Landak",
    "Kabupaten Langkat",
    "Kabupaten Lanny Jaya",
    "Kabupaten Lebak",
    "Kabupaten Lebong",
    "Kabupaten Lembata",
    "Kabupaten Lima Puluh Kota",
    "Kabupaten Lingga",
    "Kabupaten Lombok Barat",
    "Kabupaten Lombok Tengah",
    "Kabupaten Lombok Timur",
    "Kabupaten Lombok Utara",
    "Kabupaten Lumajang",
    "Kabupaten Luwu",
    "Kabupaten Luwu Timur",
    "Kabupaten Luwu Utara",
    "Kabupaten Madiun",
    "Kabupaten Magelang",
    "Kabupaten Magetan",
    "Kabupaten Mahakam Ulu",
    "Kabupaten Majalengka",
    "Kabupaten Majene",
    "Kabupaten Malaka",
    "Kabupaten Malang",
    "Kabupaten Malinau",
    "Kabupaten Maluku Barat Daya",
    "Kabupaten Maluku Tengah",
    "Kabupaten Maluku Tenggara",
    "Kabupaten Mamasa",
    "Kabupaten Mamberamo Raya",
    "Kabupaten Mamberamo Tengah",
    "Kabupaten Mamuju",
    "Kabupaten Mamuju Tengah",
    "Kabupaten Mandailing Natal",
    "Kabupaten Manggarai",
    "Kabupaten Manggarai Barat",
    "Kabupaten Manggarai Timur",
    "Kabupaten Manokwari",
    "Kabupaten Manokwari Selatan",
    "Kabupaten Mappi",
    "Kabupaten Maros",
    "Kabupaten Maybrat",
    "Kabupaten Melawi",
    "Kabupaten Mempawah",
    "Kabupaten Merangin",
    "Kabupaten Merauke",
    "Kabupaten Mesuji",
    "Kabupaten Mimika",
    "Kabupaten Minahasa",
    "Kabupaten Minahasa Selatan",
    "Kabupaten Minahasa Tenggara",
    "Kabupaten Minahasa Utara",
    "Kabupaten Mojokerto",
    "Kabupaten Morowali",
    "Kabupaten Morowali Utara",
    "Kabupaten Muara Enim",
    "Kabupaten Muaro Jambi",
    "Kabupaten Mukomuko",
    "Kabupaten Muna",
    "Kabupaten Muna Barat",
    "Kabupaten Murung Raya",
    "Kabupaten Musi Banyuasin",
    "Kabupaten Musi Rawas",
    "Kabupaten Musi Rawas Utara",
    "Kabupaten Nabire",
    "Kabupaten Nagan Raya",
    "Kabupaten Nagekeo",
    "Kabupaten Natuna",
    "Kabupaten Nduga",
    "Kabupaten Ngada",
    "Kabupaten Nganjuk",
    "Kabupaten Ngawi",
    "Kabupaten Nias",
    "Kabupaten Nias Barat",
    "Kabupaten Nias Selatan",
    "Kabupaten Nias Utara",
    "Kabupaten Nunukan",
    "Kabupaten Ogan Ilir",
    "Kabupaten Ogan Komering Ilir",
    "Kabupaten Ogan Komering Ulu",
    "Kabupaten Ogan Komering Ulu Selatan",
    "Kabupaten Ogan Komering Ulu Timur",
    "Kabupaten Pacitan",
    "Kabupaten Padang Lawas",
    "Kabupaten Padang Lawas Utara",
    "Kabupaten Padang Pariaman",
    "Kabupaten Pakpak Bharat",
    "Kabupaten Pamekasan",
    "Kabupaten Pandeglang",
    "Kabupaten Pangandaran",
    "Kabupaten Pangkajene Dan Kepulauan",
    "Kabupaten Paniai",
    "Kabupaten Parigi Moutong",
    "Kabupaten Pasaman",
    "Kabupaten Pasaman Barat",
    "Kabupaten Pasangkayu",
    "Kabupaten Paser",
    "Kabupaten Pasuruan",
    "Kabupaten Pati",
    "Kabupaten Pegunungan Arfak",
    "Kabupaten Pegunungan Bintang",
    "Kabupaten Pekalongan",
    "Kabupaten Pelalawan",
    "Kabupaten Pemalang",
    "Kabupaten Penajam Paser Utara",
    "Kabupaten Penukal Abab Lematang Ilir",
    "Kabupaten Pesawaran",
    "Kabupaten Pesisir Barat",
    "Kabupaten Pesisir Selatan",
    "Kabupaten Pidie",
    "Kabupaten Pidie Jaya",
    "Kabupaten Pinrang",
    "Kabupaten Pohuwato",
    "Kabupaten Polewali Mandar",
    "Kabupaten Ponorogo",
    "Kabupaten Poso",
    "Kabupaten Pringsewu",
    "Kabupaten Probolinggo",
    "Kabupaten Pulang Pisau",
    "Kabupaten Pulau Morotai",
    "Kabupaten Pulau Taliabu",
    "Kabupaten Puncak",
    "Kabupaten Puncak Jaya",
    "Kabupaten Purbalingga",
    "Kabupaten Purwakarta",
    "Kabupaten Purworejo",
    "Kabupaten Raja Ampat",
    "Kabupaten Rejang Lebong",
    "Kabupaten Rembang",
    "Kabupaten Rokan Hilir",
    "Kabupaten Rokan Hulu",
    "Kabupaten Rote Ndao",
    "Kabupaten Sabu Raijua",
    "Kabupaten Sambas",
    "Kabupaten Samosir",
    "Kabupaten Sampang",
    "Kabupaten Sanggau",
    "Kabupaten Sarmi",
    "Kabupaten Sarolangun",
    "Kabupaten Sekadau",
    "Kabupaten Seluma",
    "Kabupaten Semarang",
    "Kabupaten Seram Bagian Barat",
    "Kabupaten Seram Bagian Timur",
    "Kabupaten Serang",
    "Kabupaten Serdang Bedagai",
    "Kabupaten Seruyan",
    "Kabupaten Siak",
    "Kabupaten Sidenreng Rappang",
    "Kabupaten Sidoarjo",
    "Kabupaten Sigi",
    "Kabupaten Sijunjung",
    "Kabupaten Sikka",
    "Kabupaten Simalungun",
    "Kabupaten Simeulue",
    "Kabupaten Sinjai",
    "Kabupaten Sintang",
    "Kabupaten Situbondo",
    "Kabupaten Sleman",
    "Kabupaten Solok",
    "Kabupaten Solok Selatan",
    "Kabupaten Soppeng",
    "Kabupaten Sorong",
    "Kabupaten Sorong Selatan",
    "Kabupaten Sragen",
    "Kabupaten Subang",
    "Kabupaten Sukabumi",
    "Kabupaten Sukamara",
    "Kabupaten Sukoharjo",
    "Kabupaten Sumba Barat",
    "Kabupaten Sumba Barat Daya",
    "Kabupaten Sumba Tengah",
    "Kabupaten Sumba Timur",
    "Kabupaten Sumbawa",
    "Kabupaten Sumbawa Barat",
    "Kabupaten Sumedang",
    "Kabupaten Sumenep",
    "Kabupaten Supiori",
    "Kabupaten Tabalong",
    "Kabupaten Tabanan",
    "Kabupaten Takalar",
    "Kabupaten Tambrauw",
    "Kabupaten Tana Tidung",
    "Kabupaten Tana Toraja",
    "Kabupaten Tanah Bumbu",
    "Kabupaten Tanah Datar",
    "Kabupaten Tanah Laut",
    "Kabupaten Tangerang",
    "Kabupaten Tanggamus",
    "Kabupaten Tanjung Jabung Barat",
    "Kabupaten Tanjung Jabung Timur",
    "Kabupaten Tapanuli Selatan",
    "Kabupaten Tapanuli Tengah",
    "Kabupaten Tapanuli Utara",
    "Kabupaten Tapin",
    "Kabupaten Tasikmalaya",
    "Kabupaten Tebo",
    "Kabupaten Tegal",
    "Kabupaten Teluk Bintuni",
    "Kabupaten Teluk Wondama",
    "Kabupaten Temanggung",
    "Kabupaten Timor Tengah Selatan",
    "Kabupaten Timor Tengah Utara",
    "Kabupaten Toba",
    "Kabupaten Tojo Una Una",
    "Kabupaten Tolikara",
    "Kabupaten Tolitoli",
    "Kabupaten Toraja Utara",
    "Kabupaten Trenggalek",
    "Kabupaten Tuban",
    "Kabupaten Tulang Bawang",
    "Kabupaten Tulang Bawang Barat",
    "Kabupaten Tulungagung",
    "Kabupaten Wajo",
    "Kabupaten Wakatobi",
    "Kabupaten Waropen",
    "Kabupaten Way Kanan",
    "Kabupaten Wonogiri",
    "Kabupaten Wonosobo",
    "Kabupaten Yahukimo",
    "Kabupaten Yalimo",
    "Kota Administrasi Jakarta Barat",
    "Kota Administrasi Jakarta Pusat",
    "Kota Administrasi Jakarta Selatan",
    "Kota Administrasi Jakarta Timur",
    "Kota Administrasi Jakarta Utara",
    "Kota Ambon",
    "Kota Balikpapan",
    "Kota Banda Aceh",
    "Kota Bandar Lampung",
    "Kota Bandung",
    "Kota Banjar",
    "Kota Banjarbaru",
    "Kota Banjarmasin",
    "Kota Batam",
    "Kota Batu",
    "Kota Baubau",
    "Kota Bekasi",
    "Kota Bengkulu",
    "Kota Bima",
    "Kota Binjai",
    "Kota Bitung",
    "Kota Blitar",
    "Kota Bogor",
    "Kota Bontang",
    "Kota Bukittinggi",
    "Kota Cilegon",
    "Kota Cimahi",
    "Kota Cirebon",
    "Kota Denpasar",
    "Kota Depok",
    "Kota Dumai",
    "Kota Gorontalo",
    "Kota Gunungsitoli",
    "Kota Jambi",
    "Kota Jayapura",
    "Kota Kediri",
    "Kota Kendari",
    "Kota Kotamobagu",
    "Kota Kupang",
    "Kota Langsa",
    "Kota Lhokseumawe",
    "Kota Lubuk Linggau",
    "Kota Madiun",
    "Kota Magelang",
    "Kota Makassar",
    "Kota Malang",
    "Kota Manado",
    "Kota Mataram",
    "Kota Medan",
    "Kota Metro",
    "Kota Mojokerto",
    "Kota Padang",
    "Kota Padang Panjang",
    "Kota Padangsidimpuan",
    "Kota Pagar Alam",
    "Kota Palangka Raya",
    "Kota Palembang",
    "Kota Palopo",
    "Kota Palu",
    "Kota Pangkalpinang",
    "Kota Parepare",
    "Kota Pariaman",
    "Kota Pasuruan",
    "Kota Payakumbuh",
    "Kota Pekalongan",
    "Kota Pekanbaru",
    "Kota Pematangsiantar",
    "Kota Pontianak",
    "Kota Prabumulih",
    "Kota Probolinggo",
    "Kota Sabang",
    "Kota Salatiga",
    "Kota Samarinda",
    "Kota Sawahlunto",
    "Kota Semarang",
    "Kota Serang",
    "Kota Sibolga",
    "Kota Singkawang",
    "Kota Solok",
    "Kota Sorong",
    "Kota Subulussalam",
    "Kota Sukabumi",
    "Kota Sungai Penuh",
    "Kota Surabaya",
    "Kota Surakarta",
    "Kota Tangerang",
    "Kota Tangerang Selatan",
    "Kota Tanjungbalai",
    "Kota Tanjungpinang",
    "Kota Tarakan",
    "Kota Tasikmalaya",
    "Kota Tebing Tinggi",
    "Kota Tegal",
    "Kota Ternate",
    "Kota Tidore Kepulauan",
    "Kota Tomohon",
    "Kota Tual",
    "Kota Yogyakarta",
)

SCHOOLS = ['SD Negeri 3 Sokong', 'SD Negeri 8 Sokong', 'SD Negeri 33 Mataram', 'SDN 1 Sila', 'SDN 19 Mataram', 'SDN 2 Mataram', 'SDN 31 Mataram', 'SDN 36 Mataram', 'SDN 40 Mataram', 'SDN Kwang Rase', 'MI NW Dasan Tengak', 'MI Nurul Islam', 'MTs Nurul Islam Sekarbela', 'SMP Islam Riyadlul Ulum Mentokan', 'SMP Katolik Kesuma Mataram', 'SMPN 1 Denpasar', 'SMPN 1 Mataram', 'SMPN 1 Pemenang', 'SMPN 19 Mataram', 'SMPN 2 Semarang', 'SMPN 4 Gerung', 'SMPN 4 Mataram', 'SMPN 4 Pasrepan', 'SMA Katolik Kesuma Mataram', 'SMAN 4 Mataram', 'SMAN 7 Mataram', 'SDK St. Antonius Ampenan', 'SDK St. Antonius Cakranegara', 'MAN 1 Banda Aceh', 'Demo']

SCHOOL_ALIASES = {'Demo': 'Demo', 'MI NW DASAN TENGAK': 'MI NW Dasan Tengak', 'MI Nurul Islam': 'MI Nurul Islam', 'MTS NURUL ISLAM SEKARBELA': 'MTs Nurul Islam Sekarbela', 'MTs  Nurul islam sekarbela': 'MTs Nurul Islam Sekarbela', 'MTs Nurul Islam': 'MTs Nurul Islam Sekarbela', 'MTs Nurul Islam Sekarbela': 'MTs Nurul Islam Sekarbela', 'MTsNurulIslamSekarbela': 'MTs Nurul Islam Sekarbela', 'Man 1 banda aceh': 'MAN 1 Banda Aceh', 'Mrs Nurul Islam': 'MTs Nurul Islam Sekarbela', 'Mts Nurul Islam sekarbela': 'MTs Nurul Islam Sekarbela', 'Mts Nurul islam': 'MTs Nurul Islam Sekarbela', 'SD 33 Negeri': 'SD Negeri 33 Mataram', 'SD Negeri 3 Sokong': 'SD Negeri 3 Sokong', 'SD Negeri 31 Mataram': 'SDN 31 Mataram', 'SD Negeri 8 Sokong': 'SD Negeri 8 Sokong', 'SDK St. Antonius Ampenan': 'SDK St. Antonius Ampenan', 'SDK St. Antonius Cakranegara': 'SDK St. Antonius Cakranegara', 'SDN 1 SILA': 'SDN 1 Sila', 'SDN 19 Mataram': 'SDN 19 Mataram', 'SDN 2 MATARAM': 'SDN 2 Mataram', 'SDN 31 Mataram': 'SDN 31 Mataram', 'SDN 36 Mataram': 'SDN 36 Mataram', 'SDN 40 Mataram': 'SDN 40 Mataram', 'SDN Kwang Rase': 'SDN Kwang Rase', 'SMA Katolik Kesuma Mataram': 'SMA Katolik Kesuma Mataram', 'SMA Kesuma': 'SMA Katolik Kesuma Mataram', 'SMA NEGERI 7 MATARAM': 'SMAN 7 Mataram', 'SMAK': 'SMA Katolik Kesuma Mataram', 'SMAK KESUMA MATARAM': 'SMA Katolik Kesuma Mataram', 'SMAK KESUMA Mataram': 'SMA Katolik Kesuma Mataram', 'SMAK Kesuma': 'SMA Katolik Kesuma Mataram', 'SMAK Kesuma Mataram': 'SMA Katolik Kesuma Mataram', 'SMAN 4 Mataram': 'SMAN 4 Mataram', 'SMAN 7 MATARAM': 'SMAN 7 Mataram', 'SMAN 7 Mataram': 'SMAN 7 Mataram', 'SMP 4 Gerung': 'SMPN 4 Gerung', 'SMP ISLAM RIYADLUL ULUM MENTOKAN': 'SMP Islam Riyadlul Ulum Mentokan', 'SMP Katolik Kesuma Mataram': 'SMP Katolik Kesuma Mataram', 'SMPK KESUMA MATARAM': 'SMP Katolik Kesuma Mataram', 'SMPK Kesuma Mataram': 'SMP Katolik Kesuma Mataram', 'SMPK. Kesuma Mataram': 'SMP Katolik Kesuma Mataram', 'SMPN  1 Mataram': 'SMPN 1 Mataram', 'SMPN 02 Semarang': 'SMPN 2 Semarang', 'SMPN 1 Mataram': 'SMPN 1 Mataram', 'SMPN 1 Pemenang': 'SMPN 1 Pemenang', 'SMPN 19 MATARAM': 'SMPN 19 Mataram', 'SMPN 4 Gerung': 'SMPN 4 Gerung', 'SMPN 4 Mataram': 'SMPN 4 Mataram', 'SMPN 4 Pasrepan': 'SMPN 4 Pasrepan', 'Smak  Kesuma Mataram': 'SMA Katolik Kesuma Mataram', 'Smpk Kesuma Mataram': 'SMP Katolik Kesuma Mataram', 'Smpk kesuma Mataram': 'SMP Katolik Kesuma Mataram', 'Smpk kesuma mataram': 'SMP Katolik Kesuma Mataram', 'smp 1 denpasar': 'SMPN 1 Denpasar', 'smp 1 pemenang': 'SMPN 1 Pemenang', 'smp negri 1 pemenang': 'SMPN 1 Pemenang', 'smpk kesuma Mataram': 'SMP Katolik Kesuma Mataram', 'smpk kesuma mataram': 'SMP Katolik Kesuma Mataram', 'smpkkesumamataram': 'SMP Katolik Kesuma Mataram'}

CITY_ALIASES = {'Kota Mataram': 'Kota Mataram', 'Mataram': 'Kota Mataram', 'MATARAM': 'Kota Mataram', 'mataram': 'Kota Mataram', 'Ampenan': 'Kota Mataram', 'BIma': 'Kabupaten Bima', 'Banda Aceh': 'Kota Banda Aceh', 'Jaksel': 'Kota Administrasi Jakarta Selatan', 'Lombok Utara': 'Kabupaten Lombok Utara', 'pemenang': 'Kabupaten Lombok Utara', 'Lombk Barat': 'Kabupaten Lombok Barat', 'Lombok Barat': 'Kabupaten Lombok Barat', 'LOMBOK TENGAH': 'Kabupaten Lombok Tengah', 'Lombok Tengah': 'Kabupaten Lombok Tengah', 'LOMBOK TIMUR': 'Kabupaten Lombok Timur', 'Pasuruan': 'Kabupaten Pasuruan', 'Semarang': 'Kabupaten Semarang', 'Yogyakarta': 'Kota Yogyakarta', 'denpasar': 'Kota Denpasar'}


def upgrade() -> None:
    bind = op.get_bind()

    # 0) Enforce SQLite FK cascades (pysqlite does not enable them by default):
    #    deleting a user then cascades students -> practices -> attempt trees.
    #    PRAGMA foreign_keys is a no-op inside a transaction, so set it from
    #    an autocommit block (connection-scoped; stays ON afterwards, which is
    #    what the app expects).
    with op.get_context().autocommit_block():
        bind.exec_driver_sql("PRAGMA foreign_keys=ON")

    # 1) Delete the 4 junk accounts (full cascade: students, practices, attempts, ...).
    uids = [
        row[0]
        for row in bind.execute(
            text(
                "SELECT user_id FROM students "
                "WHERE school IN ('MAN 1', 'SMA 101', 'SMP1', 'Al Azhar')"
            )
        )
    ]
    if uids:
        bind.execute(
            text("DELETE FROM users WHERE id IN :ids").bindparams(bindparam("ids", expanding=True)),
            {"ids": uids},
        )

    # 2) Master tables.
    op.create_table(
        "cities",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=80), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_table(
        "schools",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=140), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # 3) Seed cities and schools (fresh UUIDv7s, in-migration).
    from framework.infra.uuid7 import uuid7

    city_ids: dict[str, str] = {}
    for name in CITIES:
        city_id = uuid7()
        city_ids[name] = city_id
        bind.execute(
            text("INSERT INTO cities (id, name, is_active, created_at) VALUES (:id, :name, 1, CURRENT_TIMESTAMP)"),
            {"id": city_id, "name": name},
        )
    school_ids: dict[str, str] = {}
    for name in SCHOOLS:
        school_id = uuid7()
        school_ids[name] = school_id
        bind.execute(
            text("INSERT INTO schools (id, name, is_active, created_at, updated_at) VALUES (:id, :name, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"),
            {"id": school_id, "name": name},
        )

    # 4) FK columns.
    for table in ("students", "teachers"):
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column("school_id", sa.String(length=36), nullable=True))
            batch.add_column(sa.Column("city_id", sa.String(length=36), nullable=True))

    # 5) Backfill via the explicit alias tables.
    for raw, canon in SCHOOL_ALIASES.items():
        school_id = school_ids[canon]
        bind.execute(text("UPDATE students SET school_id = :sid WHERE school = :raw"), {"sid": school_id, "raw": raw})
        bind.execute(text("UPDATE teachers SET school_id = :sid WHERE school = :raw"), {"sid": school_id, "raw": raw})
    for raw, canon in CITY_ALIASES.items():
        city_id = city_ids[canon]
        bind.execute(text("UPDATE students SET city_id = :cid WHERE city = :raw"), {"cid": city_id, "raw": raw})
        bind.execute(text("UPDATE teachers SET city_id = :cid WHERE city = :raw"), {"cid": city_id, "raw": raw})

    # 6) Every surviving row must resolve.
    for table in ("students", "teachers"):
        missing_school = bind.execute(text(f"SELECT COUNT(*) FROM {table} WHERE school_id IS NULL")).scalar()
        missing_city = bind.execute(text(f"SELECT COUNT(*) FROM {table} WHERE city_id IS NULL")).scalar()
        if missing_school or missing_city:
            raise RuntimeError(f"backfill gagal untuk {table}: school NULL={missing_school}, city NULL={missing_city}")

    # 7) NOT NULL + FK constraints.
    for table in ("students", "teachers"):
        with op.batch_alter_table(table) as batch:
            batch.alter_column("school_id", nullable=False)
            batch.create_foreign_key(f"fk_{table}_school_id", "schools", ["school_id"], ["id"])
            batch.create_foreign_key(f"fk_{table}_city_id", "cities", ["city_id"], ["id"])

    # 8) Drop the free-text columns.
    for table in ("students", "teachers"):
        with op.batch_alter_table(table) as batch:
            batch.drop_column("school")
            batch.drop_column("city")
            batch.drop_column("country")


def downgrade() -> None:
    bind = op.get_bind()
    for table in ("students", "teachers"):
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column("school", sa.String(length=140), nullable=True))
            batch.add_column(sa.Column("city", sa.String(length=80), nullable=True))
            batch.add_column(sa.Column("country", sa.String(length=80), nullable=True, server_default="Indonesia"))

    bind.execute(text("""
        UPDATE students
        SET school = (SELECT name FROM schools WHERE schools.id = students.school_id),
            city = (SELECT name FROM cities WHERE cities.id = students.city_id),
            country = 'Indonesia'
    """))
    bind.execute(text("""
        UPDATE teachers
        SET school = (SELECT name FROM schools WHERE schools.id = teachers.school_id),
            city = (SELECT name FROM cities WHERE cities.id = teachers.city_id),
            country = 'Indonesia'
    """))

    for table in ("students", "teachers"):
        with op.batch_alter_table(table) as batch:
            batch.drop_constraint(f"fk_{table}_city_id", type_="foreignkey")
            batch.drop_constraint(f"fk_{table}_school_id", type_="foreignkey")
            batch.drop_column("city_id")
            batch.drop_column("school_id")

    op.drop_table("schools")
    op.drop_table("cities")
