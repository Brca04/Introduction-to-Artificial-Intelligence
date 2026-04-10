# Uvod u umjetnu inteligenciju – Laboratorijska vjezba 2
# Bruno Cavor

import sys

# Ulaz podataka

def parse_clause(line): # Pretvaranje ulaza u listu literala, tj. klauzulu
    line = line.strip().lower()
    literals = []
    seen = set()

    for lit in line.split(' v '):
        lit = lit.strip()

        if lit and lit not in seen:
            literals.append(lit)
            seen.add(lit)

    return sorted(literals, key=lambda x: (x.lstrip('~'), x.startswith('~')))

def load_clauses(filepath): # Ucitavanje klauzula
    clauses = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith('#'):
                continue
            clauses.append(parse_clause(line))

    return clauses

def load_commands(filepath): # Ulaz za kuharskog asistenta
    commands = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith('#'):
                continue

            cmd_type = line[-1]
            clause_str = line[:-1].strip()
            clause = parse_clause(clause_str)
            commands.append((clause, cmd_type))

    return commands

# Pomocne funkcije za rad programa

def negate_literal(lit): # Negacija literala

    return lit[1:] if lit.startswith('~') else '~' + lit 

def clause_to_str(clause): # Ispis klauzule

    if not clause: # Ako je klauzula prazna, ispisuje NIL
        return 'NIL'
    
    return ' v '.join(sorted(clause, key=lambda x: (x.lstrip('~'), x.startswith('~')))) # Dodaje disjunkcije izmedu literala i sortira literale

def clause_in_list(clause, clause_list): # Provjera postoji li klauzula u listi klauzula

    for c in clause_list:
        if sorted(c) == sorted(clause): # Provjera jednakosti klauzula
            return True 
        
    return False

def is_subset(c1, c2): # Provjera je li klauzula c1 podskup klauzule c2
    c2_set = set(c2)

    return all(lit in c2_set for lit in c1) # Provjerava je li svaki literal iz c1 prisutan u c2

def is_tautology(clause): # Tražimo literale u klauzuli, koji sadrže atom i negaciju atoma jer time 
    clause_set = set(clause)   # dobivamo tautologiju, a s obzirom da se radi o klauzuli (disjunkciji) ostatak literala nam nije vazan 

    for lit in clause_set:
        if negate_literal(lit) in clause_set: # npr. A v ~A 
            return True


def resolve(c1, c2): 
    clause_set1 = set(c1) 
    clause_set2 = set(c2)
    resolvent = []

    for lit1 in clause_set1: # Metoda rezolucije, trazimo atom i njegovu negaciju
        if negate_literal(lit1) in clause_set2: # kada pronademo takav atom, primjenjujemo metodu rezolucije
            new_clause = sorted((set(c1) | set(c2)) - {lit1, negate_literal(lit1)}, key=lambda x: (x.lstrip('~'), x.startswith('~'))) 
            
            if not is_tautology(new_clause) and not clause_in_list(new_clause, resolvent): # Provjera tautologije (nema smisla dodati) i imamo li vec rezolventu u skupu rezolventi
                    resolvent.append(new_clause) 

    return resolvent


def resolution_refutation(premises, goal_clause): # Rezolucija opovrgavanjem

    def build_proof(): # Izgradnja dokaza nakon pronalaska NIL-a, gradimo stablo dokaza unatrag od NIL-a do premisa i negiranog cilja
        nil_idx = len(clause_list) - 1
        needed = set()
        stack = [nil_idx] 

        while stack: # Unazadno pretrazivanje u dubinu, od NIL-a do premisa i negiranog cilja
            idx = stack.pop() 

            if idx in needed: # Ako smo već obradili ovu klauzulu, preskačemo je
                continue

            needed.add(idx) # Set u kojem se nalaze indeksi klauzula koje su potrebne za dokaz

            if idx in parents: # Ako klauzula ima roditelje, dodajemo ih u stog za obradu
                stack.append(parents[idx][0])
                stack.append(parents[idx][1])

        original = sorted(i for i in needed if i not in parents) 
        derived = sorted(i for i in needed if i in parents) 

        renumber = {}
        counter = 1

        for i in original: # Popravak indeksa klauzula za ispis dokaza
            renumber[i] = counter 
            counter += 1 

        for i in derived: # Popravak indeksa klauzula za ispis dokaza
            renumber[i] = counter
            counter += 1

        lines = []

        for i in original: # Slaganje ispisa dokaza
            lines.append("{0}. {1}".format(renumber[i], clause_to_str(clause_list[i])))

        lines.append("===============")

        for i in derived:
            p1, p2 = parents[i]
            lines.append("{0}. {1} ({2}, {3})".format(renumber[i], clause_to_str(clause_list[i]), renumber[p1], renumber[p2]))
            
        lines.append("===============")
        lines.append("[CONCLUSION]: {0} is true".format(clause_to_str(goal_clause)))

        return lines

    negated_goal = [[negate_literal(lit)] for lit in goal_clause]
    clause_list = [c for c in premises if not is_tautology(c)] + negated_goal
    set_of_support = negated_goal[:]
    parents = {}

    while True:
        new = [] # new ← ∅

        for clause1 in set_of_support:
            idx1 = clause_list.index(clause1) # indeks klauzule iz skupa potpore

            for clause2 in clause_list:
                idx2 = clause_list.index(clause2) # indeks klauzule iz liste klauzula

                for new_clause in resolve(clause1, clause2): # resolvents ← plResolve(c1, c2)
                    if not new_clause: # if NIL ∈ resolvents then return true, odnosno vracamo dokaz
                        nil_idx = len(clause_list) # Indeks klauzule NIL
                        clause_list.append(new_clause) # Dodajemo NIL u listu klauzula
                        parents[nil_idx] = (idx1, idx2) # Indeks klauzula koje su dovele do NIL-a
                        return build_proof() # Vracanje dokaza
                    
                    elif not clause_in_list(new_clause, clause_list) and not clause_in_list(new_clause, new): 
                            if not any(is_subset(existing, new_clause) for existing in clause_list): # Strategija sazimanja
                                parents[len(clause_list) + len(new)] = (idx1, idx2) # Spremanje indeksa roditelja nove klauzule
                                new.append(new_clause) # new ← new ∪ resolvents

        if not new: # if new ⊆ clauses then return false, odnosno ako nema novih klauzula
            return ["[CONCLUSION]: {0} is unknown".format(clause_to_str(goal_clause))]
        
        clause_list.extend(new) #clauses ← clauses ∪ new
        set_of_support.extend(new) 


def do_resolution(clauses_file): # Poziva rezoluciju opovrgavanjem
    clauses = load_clauses(clauses_file)

    if not clauses:
        print("[CONCLUSION]: unknown")
        return
    
    premises = clauses[:-1]
    goal = clauses[-1]  

    for line in resolution_refutation(premises, goal):
        print(line)

def do_cooking(clauses_file, commands_file):
    kb = load_clauses(clauses_file) # Baza znanja
    commands = load_commands(commands_file) # Komande korisnika

    print("Constructed with knowledge:")

    for c in kb:
        print(clause_to_str(c)) # Ispis baze znanja

    for clause, cmd_type in commands: # Obrad komandi
        if cmd_type == '?':
            print("\nUser's command: {0} ?".format(clause_to_str(clause)))

            for line in resolution_refutation(list(kb), clause):
                print(line)

        elif cmd_type == '+':
            print("\nUser's command: {0} +".format(clause_to_str(clause)))
            kb.append(clause)
            print("Added {0}".format(clause_to_str(clause)))

        elif cmd_type == '-':
            print("\nUser's command: {0} -".format(clause_to_str(clause)))

            for c in kb:
                if sorted(c) == sorted(clause):
                    kb.remove(c)
                    print("removed {0}".format(clause_to_str(clause)))
                    break

if __name__ == '__main__': # Glavni program
    args = sys.argv[1:]

    if args[0] == 'resolution':
        do_resolution(args[1])
    elif args[0] == 'cooking':
        do_cooking(args[1], args[2])