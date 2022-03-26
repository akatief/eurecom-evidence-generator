from abc import ABC
from . import EvidenceRetriever
from . import Evidence, EvidencePiece

from . import FeverousDB
from . import WikiPage
import numpy as np


class FEVEROUSRetriever(EvidenceRetriever, ABC):
    '''
    Retrieves evidence specifically from the FEVEROUS DB.
    '''
    def __init__(self,
                p_dataset, 
                num_evidence,
                table_per_page=1,
                evidence_per_table=1,
                column_per_table=2,
                seed=None
                ):
        """
        :param p_dataset: path of the dataset
        """
        self.db = FeverousDB(p_dataset) #Databes that contains the entire database
        self.path_db = p_dataset #path used for extracting the dataset
        self.ids = list(self.db.get_non_empty_doc_ids()) # to be changed

        self.p_dataset = p_dataset 
        self.num_evidence = num_evidence
        self.table_per_page = table_per_page
        self.evidence_per_table = evidence_per_table
        self.column_per_table = column_per_table
        self.seed = seed


    def retrieve(self,
                data):
        '''
        Scans whole FEVEROUS dataset and returns list of Evidence objects.
        It extracts a number of evidence specified by num_evidence.
        
        1.0 shuffle the wikipedia pages ? 
            1.1 filter out the wikipedia pages with num_table < table_per_page.
            1.2 filter out the tables with header_column < column_per_table
            1.3 filter out the subtables with num_row < evidence_per_tabòe
        2.0 for page in ids:
            2.1 randomly select #table_per_page from the available tables
            2.2 extract the #num_evidence evidences

        :param data: data to retrieve evidence from
        :return: a list of Evidence objects
        '''
        #Random generator for reproducibility purposes
        rng = np.random.default_rng(self.seed)
        rng.shuffle(self.ids)

        tbl_evidences = []
        for id in self.ids[:]:
            #retrieve the page
            page_json = self.db.get_doc_json(id)
            print('%%%%%%%%%%%%%%%%%%%%%% new_id ',id)

            #parse the page in WikiPage format
            wiki_page = WikiPage(id, page_json)

            tables = wiki_page.get_tables()
            if len(tables) < self.table_per_page: continue
            rng.shuffle(tables)

            #for each table in wiki_page
            for tbl in tables:
                #print(tbl)
                # get the left indexes
                 
                #TODO possible bug: check what happen with multiple row
                header_left, table_len = self._get_index(tbl)
                output = self.get_evidence(tbl, header_left, table_len,
                                            self.column_per_table,
                                            self.evidence_per_table,
                                           strategy='random', rng=rng)

                if output is not None:
                    tbl_evidences.append(Evidence(output,
                                                    len(output),
                                                    self.table_per_page, 
                                                    self.evidence_per_table,
                                                    self.column_per_table,
                                                    self.seed))
            
            if len(tbl_evidences) >= self.num_evidence:
                break
        
        #TODO bug: more evidence than necessary
        print(f"Evidences retrieved {len(tbl_evidences)}/{self.num_evidence}")


        return tbl_evidences

    def _get_index(self, 
                   tbl):
        """
        it scan all the table to check if header on the left are present

        :param tbl: table to be scanned WikiTable
        :return header_index: list of tuple containing (header_cell_id, row_number, cell content)
        :return count: number of rows in the table
        """
        header_index = []
        count = 0
        for row in tbl.get_rows():
            count += 1
            if row.is_header_row():
                continue

            else:
                first_cell = row.get_row_cells()[0]
                if first_cell.is_header:
                    #(header_cell_id, row_number)
                    header_index.append( (first_cell.name, row.row_num, first_cell.content) )

        return header_index, count  
    
    def get_evidence(self,
                    tbl,
                    header_left,
                    table_len, 
                    num_column, 
                    num_evidence, 
                    if_header=True, 
                    strategy='random', 
                    rng=None):
        """
        it is used to extract the "meaningfull" attributes from one table at time.
        "Meaningfull" is defined by the target application.

        :param strategy: "random", "template"
        :param tbl: scanned table WikiTable
        :param header_left: list of tuple containing (header_cell_id, row_number, cell content)
        :param table_len: number of row in the table, scalar
        :param num_column: num. header columns from the table
        :param num_evidence: number of evidence retrieved from the table
        :param if_header: add or not add the header in the outpot Boolean
        :param strategy: 'random' or 'template
        :param rng: Random numpy generator
        """

        tbl_id = tbl.get_id()[-1] # 0 for first table, 1 for second table, ... 
        headers = tbl.get_header_rows() # returns multiple Row that are headers!

        #TODO bug: Pivot table not header row  'Miguel Ángel Rodríguez (squash player)'
        if len(headers) == 0: return None  

        # Not enough column
        if len(headers[0].row) < num_column: return None       

        if strategy == 'random':
            output = self._random_strategy(tbl_id,
                                            tbl,
                                            header_left,
                                            table_len,
                                            num_column,
                                            num_evidence,
                                            if_header, 
                                            rng)
        
            #TODo implement: Implement not corret tables
            if output is None: return None   
            
            selected_cells, selected_h_cells = output

            evidences = [EvidencePiece(tbl.page, c,h) for c,h in zip(selected_cells, selected_h_cells)]
                
            return evidences

        if strategy == 'template':
            #TODO implement: Implement tha algorithm for horizontal table
            assert(False)
   
    def _random_strategy(self,
                        tbl_id,
                        tbl,
                        header_left,
                        table_len,
                        num_column,
                        num_evidence,
                        if_header,
                        rng):
        
        def random_relational_table():

            def find_sub_table():

                # This is done due to the possibility of multiple
                # headers inside the table : table id => Thunder of the Gods'
                header_row_nums = [r.row_num for r in tbl.get_header_rows()] # [0, 1, 3, 4]
                i_header = rng.choice(header_row_nums) # 3
                random_row_h_index = header_row_nums.index(i_header) # index in the list associated with value => 2
                # This while is used to prevent selecting a subtable composed of zero rows
                # [H] Review scores | [H] Review scores 
                # [H] Source | [H] Rating 

                count = 0
                while True:
                    #define the last row of the subtable
                    if random_row_h_index == len(header_row_nums)-1: # We select the last possible header
                        max_row_header = table_len # the range of rows goes untill the end of the table
                    else:
                        max_row_header = header_row_nums[random_row_h_index + 1] # the range of rows ends before the last header
                    
                    len_interval = max_row_header - i_header

                    # len_interval == 1 => consecutive headers
                    # len_interval < num_evidence => not enough row to extract evidence
                    if len_interval == 1 or len_interval < num_evidence: 
                        random_row_h_index =  (random_row_h_index+1) % len(header_row_nums)
                        i_header = header_row_nums[random_row_h_index]
                    else:
                        break
                    
                    # to avoid infinite for loop
                    #"Holy See–Philippines relations"
                    if count == len(header_row_nums)*2: return None 

                    count += 1
                
                return random_row_h_index, i_header, max_row_header

            output = find_sub_table()
            if output is None: return None

            index, start_i, end_i = output
            
            # Row class associated with the index
            selected_header = tbl.get_header_rows()[index] 

            # Now we have the range of correct rows associated to that specific header
            # from [start_i + 1,  end_i ]

            #randomly choose the headers
            list_j = rng.choice( len( selected_header.row ), num_column, replace=False)
            selected_h_cells =  np.array( selected_header.row )[list_j]
          
            # Now that we have the columns we randomly select #num_evidence rows
            possible_rows = np.arange(start_i + 1,  end_i )

            if len(possible_rows) < num_evidence: return None
            
            list_i = rng.choice(possible_rows, num_evidence, replace=False)

            #TODO bug: understand if assumption on id is correct
            try: # we discard the table with different ids
                for i in list_i:
                    selected_content = [tbl.get_cell(f'cell_{tbl_id}_{i}_{j}') for j in list_j]
            except:
                print('error in retrieving the cell')
                return None

            if if_header:
                return selected_content, selected_h_cells
            else:
                return selected_content, None

        #TODO implement: Implement pivot table
        def random_entity_table():
            pass


        if len(header_left) == 0:
            return random_relational_table()
        else:
            return random_entity_table()

       