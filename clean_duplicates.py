import json
from pathlib import Path
from typing import List, Dict

def clean_duplicates(input_file: str = 'outcomes_dataset.json', 
                     output_file: str = 'outcomes_dataset_cleaned.json',
                     backup: bool = True) -> None:
    
    with open(input_file, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    print(f"Documents avant nettoyage: {len(documents)}\n")
    
    # Grouper par project_number
    by_project = {}
    for doc in documents:
        proj_num = doc.get('project_number')
        if proj_num:
            if proj_num not in by_project:
                by_project[proj_num] = []
            by_project[proj_num].append(doc)
    
    # Identifier duplicatas
    duplicates = {k: v for k, v in by_project.items() if len(v) > 1}
    
    print(f"Projets avec duplicatas: {len(duplicates)}\n")
    
    if duplicates:
        print("=" * 80)
        print("DUPLICATAS DÉTECTÉS:")
        print("=" * 80)
        
        for proj_num, docs in sorted(duplicates.items()):
            print(f"\nProjet {proj_num}: {len(docs)} versions")
            for doc in docs:
                print(f"  Batch: {doc.get('processing_batch', 'N/A')}")
                print(f"  cohort_raw: {doc.get('cohort_raw', 'N/A')}")
                print(f"  filename: {doc.get('filename', 'N/A')}")
                print()
    
    # Nettoyer: garder uniquement batch 1
    cleaned_docs = []
    seen_projects = set()
    
    for doc in documents:
        proj_num = doc.get('project_number')
        
        if not proj_num:
            cleaned_docs.append(doc)
            continue
        
        if proj_num in seen_projects:
            continue
        
        if proj_num in duplicates:
            batch_1_versions = [d for d in duplicates[proj_num] 
                               if d.get('processing_batch') == '1']
            
            if batch_1_versions:
                cleaned_docs.append(batch_1_versions[0])
                seen_projects.add(proj_num)
                print(f"Projet {proj_num}: Gardé batch 1")
            else:
                all_versions = duplicates[proj_num]
                cleaned_docs.append(all_versions[0])
                seen_projects.add(proj_num)
                print(f"Projet {proj_num}: Aucune version batch 1, gardé première version")
        else:
            cleaned_docs.append(doc)
            seen_projects.add(proj_num)
    
    print(f"\n{'=' * 80}")
    print(f"Documents après nettoyage: {len(cleaned_docs)}")
    print(f"Documents supprimés: {len(documents) - len(cleaned_docs)}")
    
    if backup:
        backup_file = input_file.replace('.json', '_backup.json')
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)
        print(f"Backup créé: {backup_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_docs, f, ensure_ascii=False, indent=2)
    
    print(f"Fichier nettoyé sauvegardé: {output_file}")

if __name__ == '__main__':
    clean_duplicates()