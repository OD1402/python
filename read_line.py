with open('/home/od/Документы//baza_winner_vtorichka_region.xml', 'r') as file:
    lines = file.readlines()[:60]
    for line in lines:
        print(line.strip())