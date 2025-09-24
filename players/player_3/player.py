from models.player import GameContext, Item, Player, PlayerSnapshot
from players.player_3.bst_player_presets import BayesianTreeBeamSearchPlayer
from players.player_3.zipper import ZipperPlayer

GLOBAL_COMPETITION_RATE = 0.5


# class Player3(Player):
# 	def __init__( self,
# 		snapshot: PlayerSnapshot,
# 		ctx: GameContext,
# 		initial_competition_rate: float = GLOBAL_COMPETITION_RATE,
# 	) -> None:
# 		super().__init__(
# 			snapshot=snapshot,
# 			ctx=ctx,
# 			initial_competition_rate=initial_competition_rate,
# 			depth=3,
# 			breadth=16,
# 			# static_threhold=GLOBAL_BST_THREHOLD,
# 		)
#         self.mode = "TEST"

class Player3(Player):
    def __init__(self, snapshot: PlayerSnapshot, ctx: GameContext):
        super().__init__(snapshot, ctx)
        # Make one instance of each strategy
        self.bst_player = BayesianTreeBeamSearchPlayer(snapshot, ctx, depth=3, breadth=16)
        self.zipper_player = ZipperPlayer(snapshot, ctx)
        self.mode = "TEST"
        temp_subject_count = max(max(self.memory_bank, key=lambda x: x.subjects).subjects)
        self.subject_count = temp_subject_count
    
    def is_valid_sinlge_ribbon(self, history):
        if len(history)==0:
            return True
        if len(history)<=2:
            return True
        if history[0]==None:
            return self.is_valid_sinlge_ribbon(history[1:])
        if history[1]==None:
            return self.is_valid_sinlge_ribbon(history[2:])
        if history[0].subjects[0]==history[1].subjects[0]:
            return False
        for i in range(2, len(history)):
            if history[i]==None:
                return self.is_valid_sinlge_ribbon(history[i+1:])
            if history[i].subjects[0]!=history[i-2].subjects[0]:
                return False
        return True
        

    def is_valid_ribbon(self, history):
        if len(history)==0:
            return True
        for i in range(len(history)-1):
            if history[i]==None and history[i+1]==None:
                return False
        for element in history:
            if element == None:
                continue
            if len(element.subjects)==2:
                return False
        return self.is_valid_sinlge_ribbon(history)

    def propose_item(self, history):
        # print("start", self.mode)

        if self.mode == "BAY":
            item = self.bst_player.propose_item(history)
            return item
        elif self.mode == "ZIP":
            #Im Zip, do a quick check to make sure the 

            item = self.zipper_player.propose_item(history)
            if item == None and len(history)>1 and history[-1]==None:
                self.mode = "BAY"
                item = self.bst_player.propose_item(history)
            
            for element in history:
                if element == None:
                    continue
                if len(element.subjects)==2:
                    self.mode = "BAY"
                    item = self.bst_player.propose_item(history)

            return item
        
        if self.conversation_length<25:
            self.mode = "BAY"
            item = self.bst_player.propose_item(history)
            return item
        if len(self.memory_bank)*self.number_of_players < 4*self.conversation_length:
            self.mode = "BAY"
            item = self.bst_player.propose_item(history)
            return item
        if self.conversation_length < 75 and self.subject_count>15:
            self.mode = "BAY"
            item = self.bst_player.propose_item(history)
            return item
        if self.conversation_length < 300 and self.subject_count>40:
            self.mode = "BAY"
            item = self.bst_player.propose_item(history)
            return item
        
        #Check to see if the history thus far is a valid ribbon, If so continue with the zipper. 
        is_valid = self.is_valid_ribbon(history)

        if is_valid:
            if len(history)==10:
                self.mode = "ZIP"
            
            #After 10, if the zipper is still valid, 
            item = self.zipper_player.propose_item(history)
            return item
        else:
            self.mode = "BAY"
            item = self.bst_player.propose_item(history)
            return item
