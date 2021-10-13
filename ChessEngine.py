import copy
"""
store information about current state of game
determine valid move
keep movelog
"""

"""
TODO: fix enpassant UI bug in move class
"""


class GameState:
    def __init__(self):
        # 8x8 2d list, each element has 2 characters
        # first char for which color
        # second char for which piece, R = rook, N = knight, B = bishop, K = knight, Q = queen
        # "--" is emtpy cell

        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]
        self.moveFuntions = {'p': self.getPawnMoves, "R": self.getRookMoves, "N": self.getKnightMoves,
                             "B": self.getBishopMoves, "K": self.getKingMoves, "Q": self.getQueenMoves}
        self.whiteToMove = True
        self.moveLog = []
        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)
        self.checkMate = False
        self.staleMate = False
        self.gameOver = False
        # coordiantes for the square where en passant capture is possible
        self.enpassantPossible = ()
        self.enpassantPossibleLog = [self.enpassantPossible]
        self.currentCastlingRight = CastleRights(True, True, True, True)
        self.castleRightsLog = [CastleRights(
            self.currentCastlingRight.wks, self.currentCastlingRight.bks, self.currentCastlingRight.wqs, self.currentCastlingRight.bqs)]
        # self.protects = [[]]
        # self.threatens = [[]]
        # self.squaresCanMoveTo = [[]]

    def makeMove(self, move):
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move)  # log the move to undo
        self.whiteToMove = not self.whiteToMove  # switch turns
        # update king location
        if move.pieceMoved == "wK":
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == "bK":
            self.blackKingLocation = (move.endRow, move.endCol)
        # pawn promo
        if move.pawnPromotion:
            self.board[move.endRow][move.endCol] = move.pieceMoved[0] + "Q"
        # enpassant
        if move.isEnpassantMove:
            self.board[move.startRow][move.endCol] = "--"  # capture pawn
        # update enpassantPossible
        # 2 squares advance => enpassant possible
        if move.pieceMoved[1] == "p" and abs(move.startRow - move.endRow) == 2:
            self.enpassantPossible = (
                (move.startRow + move.endRow)//2, move.startCol)
        else:
            self.enpassantPossible = ()

        # castle move
        if move.isCastleMove:
            if move.endCol - move.startCol == 2:  # king side castle
                self.board[move.endRow][move.endCol -
                                        1] = self.board[move.endRow][move.endCol+1]  # move rook
                self.board[move.endRow][move.endCol+1] = "--"  # delete rook
            else:  # queen side castle
                self.board[move.endRow][move.endCol +
                                        1] = self.board[move.endRow][move.endCol-2]  # move rook
                self.board[move.endRow][move.endCol-2] = "--"  # delete rook
        # update castling rights
        self.updateCastleRights(move)
        self.castleRightsLog.append(CastleRights(
            self.currentCastlingRight.wks, self.currentCastlingRight.bks, self.currentCastlingRight.wqs, self.currentCastlingRight.bqs))

        self.enpassantPossibleLog.append(self.enpassantPossible)

    def undoMove(self):
        if len(self.moveLog) != 0:
            move = self.moveLog.pop()
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            self.whiteToMove = not self.whiteToMove  # switch turns

            # update king position
            if move.pieceMoved == "wK":
                self.whiteKingLocation = (move.startRow, move.startCol)
            elif move.pieceMoved == "bK":
                self.blackKingLocation = (move.startRow, move.startCol)

            # undo en passant
            if move.isEnpassantMove:
                # leave landing square blank
                self.board[move.endRow][move.endCol] = "--"
                self.board[move.startRow][move.endCol] = move.pieceCaptured

            self.enpassantPossibleLog.pop()
            self.enpassantPossible = self.enpassantPossibleLog[-1]

            # undo castling rights
            self.castleRightsLog.pop()
            #newRights = self.castleRightsLog[-1]
            #self.currentCastlingRight = CastleRights(newRights.wks, newRights.bks, newRights.wqs, newRights.bqs)

            # undo castle moves
            if move.isCastleMove:
                if move.endCol - move.startCol == 2:  # king side
                    self.board[move.endRow][move.endCol +
                                            1] = self.board[move.endRow][move.endCol-1]
                    self.board[move.endRow][move.endCol-1] = "--"
                else:  # queenside
                    self.board[move.endRow][move.endCol -
                                            2] = self.board[move.endRow][move.endCol+1]
                    self.board[move.endRow][move.endCol+1] = "--"

            # set the current castle rights to the last one in the list
            CastleRights = copy.deepcopy(self.castleRightsLog[-1])
            self.currentCastlingRight = CastleRights

            if self.staleMate and self.gameOver:
                self.staleMate = not self.staleMate
                self.gameOver = not self.gameOver
            elif self.checkMate and self.gameOver:
                self.checkMate = not self.checkMate
                self.gameOver = not self.gameOver

            self.checkMate = False
            self.staleMate = False

    def updateCastleRights(self, move):
        """
        update the castle rights given the move
        """

        # move King
        if move.pieceMoved == "wK":
            self.currentCastlingRight.wks = False
            self.currentCastlingRight.wqs = False
        if move.pieceMoved == "bK":
            self.currentCastlingRight.bks = False
            self.currentCastlingRight.bqs = False

        # move Rooks
        elif move.pieceMoved == "wR":
            if move.startRow == 7:
                if move.startCol == 0:  # white left rook
                    self.currentCastlingRight.wqs = False
                elif move.startCol == 7:  # white right rook
                    self.currentCastlingRight.wks = False
        elif move.pieceMoved == "bR":
            if move.startRow == 0:
                if move.startCol == 0:  # black left rook
                    self.currentCastlingRight.bqs = False
                elif move.startCol == 7:  # black right rook
                    self.currentCastlingRight.bks = False

        # Rooks are captured
        if move.pieceCaptured == "wR":
            if move.endRow == 7:
                if move.endCol == 0:  # white left rook
                    self.currentCastlingRight.wqs = False
                elif move.endCol == 7:  # white right rook
                    self.currentCastlingRight.wks = False
        elif move.pieceCaptured == "bR":
            if move.endRow == 0:
                if move.endCol == 0:  # black left rook
                    self.currentCastlingRight.bqs = False
                elif move.endCol == 7:  # black right rook
                    self.currentCastlingRight.bks = False

    def getValidMoves(self):
        """# print for debug
        for log in self.castleRightsLog:
            print(log.wks, log.wqs, log.bks, log.bqs, end="\n")
        """
        moves = []
        self.inCheck, self.pins, self.checks = self.checkForPinsAndChecks()
        if self.whiteToMove:
            kingRow = self.whiteKingLocation[0]
            kingCol = self.whiteKingLocation[1]
            self.getCastleMoves(kingRow, kingCol, moves)

        else:
            kingRow = self.blackKingLocation[0]
            kingCol = self.blackKingLocation[1]
            self.getCastleMoves(kingRow, kingCol, moves)

        if self.inCheck:
            if len(self.checks) == 1:  # 1 check => move King or block the check
                moves = self.getAllPossibleMoves()
                check = self.checks[0]
                checkRow = check[0]
                checkCol = check[1]
                # piece causing check
                pieceChecking = self.board[checkRow][checkCol]
                validSquares = []  # squares that pieces can move to
                # if it's knight => take kngiht or move, other could use a piece to block
                if pieceChecking[1] == "N":
                    validSquares = [(checkRow, checkCol)]
                else:
                    for i in range(1, 8):
                        # check[2] and check[3] are the check directions
                        # check[2] and [3] is check direction
                        validSquare = (
                            kingRow + check[2]*i, kingCol + check[3] * i)
                        validSquares.append(validSquare)
                        # get to checking piece
                        if validSquare[0] == checkRow and validSquare[1] == checkCol:
                            break
                # get rid of any move that don't block check or move king
                # go through backwards when you are removing from a list as iterating
                for i in range(len(moves) - 1, -1, -1):
                    # not move king => block or capture checking piece
                    if moves[i].pieceMoved[1] != "K":
                        # move doesn't block check or capture piece
                        if not (moves[i].endRow, moves[i].endCol) in validSquares:
                            moves.remove(moves[i])
            else:  # double check => move King
                self.getKingMoves(kingRow, kingCol, moves)
        else:  # not in check => all moves are valid
            moves = self.getAllPossibleMoves()
            if self.whiteToMove:
                self.getCastleMoves(
                    self.whiteKingLocation[0], self.whiteKingLocation[1], moves)
            else:
                self.getCastleMoves(
                    self.blackKingLocation[0], self.blackKingLocation[1], moves)

        if len(moves) == 0:
            if self.inCheck:
                self.checkMate = True
                self.gameOver = True

            else:
                self.staleMate = True
                self.gameOver = True
        else:
            self.checkMate = False
            self.staleMate = False

        return moves

    def inCheck(self):
        """
        Determine if the enemy can attack the square r,c
        """
        if self.whiteToMove:
            return self.squareUnderAttack(self.whiteKingLocation[0], self.whiteKingLocation[1])
        else:
            return self.squareUnderAttack(self.blackKingLocation[0], self.blackKingLocation[1])

    def squareUnderAttack(self, r, c):
        self.whiteToMove = not self.whiteToMove
        oppMoves = self.getAllPossibleMoves()
        self.whiteToMove = not self.whiteToMove
        for move in oppMoves:
            if move.endRow == r and move.endCol == c:
                return True
        return False

    def getAllPossibleMoves(self):
        """
        All moves without consider checks
        """
        moves = []
        for r in range(len(self.board)):  # number of rows
            for c in range(len(self.board[r])):  # number of cols
                turn = self.board[r][c][0]
                if (turn == "w" and self.whiteToMove) or (turn == "b" and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    # calls the moveFunctions for correct pieces
                    self.moveFuntions[piece](r, c, moves)
        return moves

    def getPawnMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.whiteToMove:
            moveAmount = -1
            startRow = 6
            backRow = 0
            enemyColor = "b"
            kingRow, kingCol = self.whiteKingLocation
        else:
            moveAmount = 1
            startRow = 1
            backRow = 7
            enemyColor = "w"
            kingRow, kingCol = self.blackKingLocation

        pawnPromotion = False

        if self.board[r+moveAmount][c] == "--":  # 1 square move
            if not piecePinned or pinDirection == (moveAmount, 0):
                if r+moveAmount == backRow:
                    pawnPromotion = True
                moves.append(Move((r, c), (r+moveAmount, c),
                             self.board, pawnPromotion=pawnPromotion))
                # 2 squares moves
                if r == startRow and self.board[r+2*moveAmount][c] == "--":
                    moves.append(Move((r, c), (r+2*moveAmount, c), self.board))

        # CAPTURES
        if c - 1 >= 0:
            # capture black piece upper diagonal left
            if not piecePinned or pinDirection == (moveAmount, -1):
                if self.board[r+moveAmount][c-1][0] == enemyColor:
                    if r+moveAmount == backRow:
                        pawnPromotion = True
                    moves.append(Move((r, c), (r+moveAmount, c-1),
                                      self.board, pawnPromotion=pawnPromotion))
                elif (r+moveAmount, c-1) == self.enpassantPossible:
                    attackingPiece = blockingPiece = False
                    if kingRow == r:
                        if kingCol < c:
                            insideRange = range(kingCol + 1, c-1)
                            outsideRange = range(c+1, 8)
                        else:
                            insideRange = range(kingCol - 1, c, -1)
                            outsideRange = range(c-2, -1, -1)
                        for i in insideRange:
                            if self.board[r][i] != "--":
                                blockingPiece = True
                        for i in outsideRange:
                            square = self.board[r][i]
                            if square[0] == enemyColor and (square[1] == "R" or square[1] == "Q"):
                                attackingPiece = True
                            elif square != "--":
                                blockingPiece = True

                    if not attackingPiece or blockingPiece:
                        moves.append(Move((r, c), (r+moveAmount, c-1),
                                     self.board, isEnpassantMove=True))

        if c + 1 <= 7:  # capture right
            if not piecePinned or pinDirection == (moveAmount, 1):
                if self.board[r+moveAmount][c+1][0] == enemyColor:
                    if r+moveAmount == backRow:
                        pawnPromotion = True
                    moves.append(Move((r, c), (r+moveAmount, c+1),
                                      self.board, pawnPromotion=pawnPromotion))
                elif (r+moveAmount, c+1) == self.enpassantPossible:
                    attackingPiece = blockingPiece = False
                    if kingRow == r:
                        if kingCol < c:
                            insideRange = range(kingCol + 1, c)
                            outsideRange = range(c + 2, 8)
                        else:
                            insideRange = range(kingCol - 1, c + 1, -1)
                            outsideRange = range(c - 1, -1, -1)
                        for i in insideRange:
                            if self.board[r][i] != "--":
                                blockingPiece = True
                        for i in outsideRange:
                            square = self.board[r][i]
                            if square[0] == enemyColor and (square[1] == "R" or square[1] == "Q"):
                                attackingPiece = True
                            elif square != "--":
                                blockingPiece = True

                    if not attackingPiece or blockingPiece:
                        moves.append(Move((r, c), (r+moveAmount, c+1),
                                     self.board, isEnpassantMove=True))

    def getRookMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                # can't remove queen from pin on rook moves, only remove on bishop moves
                if self.board[r][c][1] != "Q":
                    self.pins.remove(self.pins[i])
                break

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))
        enemyColor = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:  # in board
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":  # empty space at destination
                            moves.append(
                                Move((r, c), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor:  # enemy piece at destination
                            moves.append(
                                Move((r, c), (endRow, endCol), self.board))
                            break
                        else:  # ally piece at destination
                            break
                else:  # off board
                    break

    def getKnightMoves(self, r, c, moves):
        piecePinned = False
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                self.pins.remove(self.pins[i])
                break

        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2),
                       (1, -2), (1, 2), (2, -1), (2, 1))
        allyColor = "w" if self.whiteToMove else "b"
        for m in knightMoves:
            endRow = r + m[0]
            endCol = c + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                if not piecePinned:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] != allyColor:
                        moves.append(
                            Move((r, c), (endRow, endCol), self.board))

    def getBishopMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        enemyColor = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:  # in board
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":  # empty space at destination
                            moves.append(
                                Move((r, c), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor:  # enemy piece at destination
                            moves.append(
                                Move((r, c), (endRow, endCol), self.board))
                            break
                        else:  # ally piece at destination
                            break
                else:  # off board
                    break

    def getQueenMoves(self, r, c, moves):
        self.getRookMoves(r, c, moves)
        self.getBishopMoves(r, c, moves)

    def getKingMoves(self, r, c, moves):
        rowMoves = (-1, -1, -1, 0, 0, 1, 1, 1)
        colMoves = (-1, 0, 1, -1, 1, -1, 0, 1)
        allyColor = "w" if self.whiteToMove else "b"
        for i in range(8):
            endRow = r + rowMoves[i]
            endCol = c + colMoves[i]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                # not an ally piece (empty or enemy)
                if endPiece[0] != allyColor:
                    if allyColor == "w":
                        self.whiteKingLocation = (endRow, endCol)
                    else:
                        self.blackKingLocation = (endRow, endCol)
                    inCheck, pins, checks = self.checkForPinsAndChecks()
                    if not inCheck:
                        moves.append(
                            Move((r, c), (endRow, endCol), self.board))
                    # place king back on original location
                    if allyColor == "w":
                        self.whiteKingLocation = (r, c)
                    else:
                        self.blackKingLocation = (r, c)

    def getCastleMoves(self, r, c, moves):
        if self.squareUnderAttack(r, c):
            return
        if (self.whiteToMove and self.currentCastlingRight.wks) or (not self.whiteToMove and self.currentCastlingRight.bks):
            self.getKingsideCastleMoves(r, c, moves)
        if (self.whiteToMove and self.currentCastlingRight.wqs) or (not self.whiteToMove and self.currentCastlingRight.bqs):
            self.getQueensideCastleMoves(r, c, moves)

    def getKingsideCastleMoves(self, r, c, moves):
        if self.board[r][c+1] == "--" and self.board[r][c+2] == "--":
            if not self.squareUnderAttack(r, c+1) and not self.squareUnderAttack(r, c+2):
                moves.append(Move((r, c), (r, c+2),
                             self.board, isCastleMove=True))

    def getQueensideCastleMoves(self, r, c, moves):
        if self.board[r][c-1] == "--" and self.board[r][c-2] == "--" and self.board[r][c-3] == "--":
            if not self.squareUnderAttack(r, c-1) and not self.squareUnderAttack(r, c-2):
                moves.append(Move((r, c), (r, c-2),
                             self.board, isCastleMove=True))

    def checkForPinsAndChecks(self):
        pins = []  # squares where allied piece are pinned and direction pinned from
        checks = []  # enemy square checking ally king
        inCheck = False
        if self.whiteToMove:
            enemyColor = "b"
            allyColor = "w"
            startRow = self.whiteKingLocation[0]
            startCol = self.whiteKingLocation[1]
        else:
            enemyColor = "w"
            allyColor = "b"
            startRow = self.blackKingLocation[0]
            startCol = self.blackKingLocation[1]

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1),
                      (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            d = directions[j]
            possiblePin = ()  # reset possible Pin
            for i in range(1, 8):
                endRow = startRow + d[0]*i
                endCol = startCol + d[1]*i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] == allyColor and endPiece[1] != "K":
                        if possiblePin == ():  # 1st allied piece could be pinned
                            possiblePin = (endRow, endCol, d[0], d[1])
                        else:  # 2nd ally piece so no pin or check possible in the direction
                            break
                    elif endPiece[0] == enemyColor:
                        type = endPiece[1]
                        # 5 cases:
                        # 1. vertically or horrizontally away from king is a rook
                        # 2. diagonally away from king is a bishop
                        # 3. 1 square diagonally away from king is a pawn
                        # 4. any direction from king is a queen
                        # 5. any direction from king is enemy king
                        if (0 <= j <= 3 and type == "R") or \
                            (4 <= j <= 7 and type == "B") or \
                            (i == 1 and type == "p" and ((enemyColor == "w" and 6 <= j <= 7) or (enemyColor == "b" and 4 <= j <= 5))) or \
                                (type == "Q") or (i == 1 and type == "K"):
                            if possiblePin == ():  # no piece blocking
                                inCheck = True
                                checks.append((endRow, endCol, d[0], d[1]))
                                break
                            else:  # piece blocking => pin
                                pins.append(possiblePin)
                                break
                        else:  # enemy piece not applying check
                            break
                else:  # off board
                    break
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2),
                       (1, -2), (1, 2), (2, -1), (2, 1))
        for m in knightMoves:
            endRow = startRow + m[0]
            endCol = startCol + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] == enemyColor and endPiece[1] == "N":
                    inCheck = True
                    checks.append((endRow, endCol, m[0], m[1]))
        return inCheck, pins, checks


class CastleRights():
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Move:
    ranksToRows = {"1": 7, "2": 6, "3": 5,
                   "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}
    filesToCols = {"a": 0, "b": 1, "c": 2,
                   "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, startSq, endSq, board, isEnpassantMove=False, pawnPromotion=False, isCastleMove=False):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        # pawn promo
        self.pawnPromotion = (self.pieceMoved == "wp" and self.endRow == 0) or (
            self.pieceMoved == "bp" and self.endRow == 7)
        # en passant
        self.isEnpassantMove = isEnpassantMove
        if self.isEnpassantMove:
            self.pieceCaptured = "wp" if self.pieceMoved == "bp" else "bp"
        # Castle move
        self.isCastleMove = isCastleMove
        # Capture move
        self.isCapture = self.pieceCaptured != "--"
        # move ID
        self.moveID = self.startRow*1000 + self.startCol * \
            100 + self.endRow*10 + self.endCol*1

    """
    Over equals method
    """

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getChessNotation(self):
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)

    def getRankFile(self, r, c):
        return self.colsToFiles[c] + self.rowsToRanks[r]

    def __str__(self) -> str:
        # castle move
        if self.isCastleMove:
            return "O-O" if self.endCol == 6 else "O-O-O"

        endSquare = self.getRankFile(self.endRow, self.endCol)

        if self.pieceMoved[1] == "p":
            if self.isCapture:
                return self.colsToFiles[self.startCol] + "x" + endSquare
            else:
                return endSquare

        moveString = self.pieceMoved[1]
        if self.isCapture:
            moveString += "x"
        return moveString + endSquare
