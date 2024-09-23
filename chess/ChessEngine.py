class GameState:
    def __init__(self):
        """
        Lưu trữ tất cả thông tin về trạng thái hiện tại của trò chơi cờ.
        Xác định các nước đi hợp lệ ở trạng thái hiện tại.
        Nó sẽ giữ bảng ghi các nước đi.
        """
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]
        self.moveFunctions = {"p": self.getPawnMoves, "R": self.getRookMoves, "N": self.getKnightMoves,
                              "B": self.getBishopMoves, "Q": self.getQueenMoves, "K": self.getKingMoves}
        self.white_to_move = True
        self.move_log = []
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)
        self.checkmate = False
        self.stalemate = False
        self.in_check = False
        self.pins = []
        self.checks = []
        self.enpassant_possible = ()  # tọa độ cho ô nơi di chuyển en-passant là có thể
        self.enpassant_possible_log = [self.enpassant_possible]
        self.current_castling_rights = CastleRights(True, True, True, True)
        self.castle_rights_log = [CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                               self.current_castling_rights.wqs, self.current_castling_rights.bqs)]

    def makeMove(self, move):
        """
        Thực hiện một nước đi được cung cấp.

        (Điều này sẽ không hoạt động cho việc đổi cờ, thăng cấp tốt và en-passant)
        """
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)  # ghi lại nước đi để có thể hoàn tác sau này
        self.white_to_move = not self.white_to_move  # chuyển người chơi
        # cập nhật vị trí vua nếu di chuyển
        if move.piece_moved == "wK":
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_location = (move.end_row, move.end_col)

        # thăng cấp tốt
        if move.is_pawn_promotion:
            # nếu không phải là is_AI:
            #    promoted_piece = input("Thăng cấp thành Q, R, B hoặc N:") #chuyển điều này vào UI sau này
            #    self.board[move.end_row][move.end_col] = move.piece_moved[0] + promoted_piece
            # nhưng:
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + "Q"

        # di chuyển enpassant
        if move.is_enpassant_move:
            self.board[move.start_row][move.end_col] = "--"  # bắt con tốt

        # cập nhật biến enpassant_possible
        if move.piece_moved[1] == "p" and abs(move.start_row - move.end_row) == 2:  # chỉ ở 2 bước tốt
            self.enpassant_possible = ((move.start_row + move.end_row) // 2, move.start_col)
        else:
            self.enpassant_possible = ()

        # di chuyển quân Xe
        if move.is_castle_move:
            if move.end_col - move.start_col == 2:  # di chuyển quân Xe bên phải vua
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][
                    move.end_col + 1]  # di chuyển xe đến ô mới
                self.board[move.end_row][move.end_col + 1] = '--'  # xóa xe cũ
            else:  # di chuyển quân Xe bên trái vua
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][
                    move.end_col - 2]  # di chuyển xe đến ô mới
                self.board[move.end_row][move.end_col - 2] = '--'  # xóa xe cũ

        self.enpassant_possible_log.append(self.enpassant_possible)

        # cập nhật quyền quân Xe - mỗi khi có một nước đi xe hoặc vua
        self.updateCastleRights(move)
        self.castle_rights_log.append(CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                                   self.current_castling_rights.wqs, self.current_castling_rights.bqs))

    def undoMove(self):
        """
        Hoàn tác nước đi cuối cùng
        """
        if len(self.move_log) != 0:  # đảm bảo rằng có một nước đi để hoàn tác
            move = self.move_log.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_to_move = not self.white_to_move  # đổi người chơi
            # cập nhật vị trí của vua nếu cần
            if move.piece_moved == "wK":
                self.white_king_location = (move.start_row, move.start_col)
            elif move.piece_moved == "bK":
                self.black_king_location = (move.start_row, move.start_col)
            # hoàn tác di chuyển en passant
            if move.is_enpassant_move:
                self.board[move.end_row][move.end_col] = "--"  # để ô đích trống
                self.board[move.start_row][move.end_col] = move.piece_captured

            self.enpassant_possible_log.pop()
            self.enpassant_possible = self.enpassant_possible_log[-1]

            # hoàn tác quyền castle 
            self.castle_rights_log.pop()  # loại bỏ quyền castle  mới từ nước đi mà chúng ta đang hoàn tác
            self.current_castling_rights = self.castle_rights_log[
                -1]  # đặt quyền quân  hiện tại thành quyền castle  cuối cùng trong danh sách
            # hoàn tác nước đi castle 
            if move.is_castle_move:
                if move.end_col - move.start_col == 2:  # phía bên phải
                    self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                    self.board[move.end_row][move.end_col - 1] = '--'
                else:  # phía bên trái
                    self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                    self.board[move.end_row][move.end_col + 1] = '--'
            self.checkmate = False
            self.stalemate = False

    def updateCastleRights(self, move):
        """
        Cập nhật quyền castle dựa trên nước đi
        """
        if move.piece_captured == "wR":
            if move.end_col == 0:  # castle bên trái
                self.current_castling_rights.wqs = False
            elif move.end_col == 7:  # castle bên phải
                self.current_castling_rights.wks = False
        elif move.piece_captured == "bR":
            if move.end_col == 0:  # castle bên trái
                self.current_castling_rights.bqs = False
            elif move.end_col == 7:  # castle bên phải
                self.current_castling_rights.bks = False

        if move.piece_moved == 'wK':
            self.current_castling_rights.wqs = False
            self.current_castling_rights.wks = False
        elif move.piece_moved == 'bK':
            self.current_castling_rights.bqs = False
            self.current_castling_rights.bks = False
        elif move.piece_moved == 'wR':
            if move.start_row == 7:
                if move.start_col == 0:  # xe bên trái
                    self.current_castling_rights.wqs = False
                elif move.start_col == 7:  # xe bên phải
                    self.current_castling_rights.wks = False
        elif move.piece_moved == 'bR':
            if move.start_row == 0:
                if move.start_col == 0:  # xe bên trái
                    self.current_castling_rights.bqs = False
                elif move.start_col == 7:  # xe bên phải
                    self.current_castling_rights.bks = False

    def getValidMoves(self):
        """
        Tất cả các nước đi có xem xét tình trạng chiếu.
        """
        temp_castle_rights = CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                          self.current_castling_rights.wqs, self.current_castling_rights.bqs)
        # thuật toán nâng cao
        moves = []
        self.in_check, self.pins, self.checks = self.checkForPinsAndChecks()

        if self.white_to_move:
            king_row = self.white_king_location[0]
            king_col = self.white_king_location[1]
        else:
            king_row = self.black_king_location[0]
            king_col = self.black_king_location[1]
        if self.in_check:
            if len(self.checks) == 1:  # chỉ có 1 chiếu, chặn chiếu hoặc di chuyển vua
                moves = self.getAllPossibleMoves()
                # để chặn chiếu bạn phải đặt một quân cờ vào một trong các ô giữa quân địch và vua của bạn
                check = self.checks[0]  # thông tin chiếu
                check_row = check[0]
                check_col = check[1]
                piece_checking = self.board[check_row][check_col]
                valid_squares = []  # các ô mà quân cờ có thể di chuyển đến
                # nếu là mã, phải bắt mã hoặc di chuyển vua của bạn, các quân cờ khác có thể bị chặn
                if piece_checking[1] == "N":
                    valid_squares = [(check_row, check_col)]
                else:
                    for i in range(1, 8):
                        valid_square = (king_row + check[2] * i,
                                        king_col + check[3] * i)  # check[2] và check[3] là hướng của chiếu
                        valid_squares.append(valid_square)
                        if valid_square[0] == check_row and valid_square[
                            1] == check_col:  # một khi bạn đến quân và chiếu
                            break
                # loại bỏ bất kỳ nước đi nào không chặn chiếu hoặc di chuyển vua
                for i in range(len(moves) - 1, -1, -1):  # duyệt qua danh sách theo chiều ngược lại khi loại bỏ các phần tử
                    if moves[i].piece_moved[1] != "K":  # nước đi không di chuyển vua nên phải chặn hoặc bắt
                        if not (moves[i].end_row,
                                moves[i].end_col) in valid_squares:  # nước đi không chặn hoặc bắt quân cờ
                            moves.remove(moves[i])
            else:  # chiếu kép, vua phải di chuyển
                self.getKingMoves(king_row, king_col, moves)
        else:  # không bị chiếu - tất cả các nước đi đều ổn
            moves = self.getAllPossibleMoves()
            if self.white_to_move:
                self.getCastleMoves(self.white_king_location[0], self.white_king_location[1], moves)
            else:
                self.getCastleMoves(self.black_king_location[0], self.black_king_location[1], moves)

        if len(moves) == 0:
            if self.inCheck():
                self.checkmate = True
            else:
                # TODO hoà cờ khi các nước đi lặp lại
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        self.current_castling_rights = temp_castle_rights
        return moves

    def inCheck(self):
        """
        Xác định nếu một người chơi hiện tại đang bị chiếu
        """
        if self.white_to_move:
            return self.squareUnderAttack(self.white_king_location[0], self.white_king_location[1])
        else:
            return self.squareUnderAttack(self.black_king_location[0], self.black_king_location[1])

    def squareUnderAttack(self, row, col):
        """
        Xác định xem đối thủ có thể tấn công ô hàng col không
        """
        self.white_to_move = not self.white_to_move  # chuyển sang quan điểm của đối thủ
        opponents_moves = self.getAllPossibleMoves()
        self.white_to_move = not self.white_to_move
        for move in opponents_moves:
            if move.end_row == row and move.end_col == col:  # ô đang bị tấn công
                return True
        return False

    def getAllPossibleMoves(self):
        """
        Tất cả các nước đi mà không xem xét chiếu
        """
        moves = []
        for row in range(len(self.board)):
            for col in range(len(self.board[row])):
                turn = self.board[row][col][0]
                if (turn == "w" and self.white_to_move) or (turn == "b" and not self.white_to_move):
                    piece = self.board[row][col][1]
                    self.moveFunctions[piece](row, col, moves)  # gọi hàm di chuyển phù hợp dựa trên loại quân cờ
        return moves


    def checkForPinsAndChecks(self):
        pins = []  # các ô bị giữ và hướng bị giữ từ đó
        checks = []  # các ô mà đối thủ áp dụng chiếu
        in_check = False
        if self.white_to_move:
            enemy_color = "b"
            ally_color = "w"
            start_row = self.white_king_location[0]
            start_col = self.white_king_location[1]
        else:
            enemy_color = "w"
            ally_color = "b"
            start_row = self.black_king_location[0]
            start_col = self.black_king_location[1]
        # kiểm tra ra khỏi vua để tìm các nước bị giữ và chiếu, giữ kỷ lục các nước bị giữ
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            direction = directions[j]
            possible_pin = ()  # đặt lại các nước bị giữ có thể
            for i in range(1, 8):
                end_row = start_row + direction[0] * i
                end_col = start_col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] == ally_color and end_piece[1] != "K":
                        if possible_pin == ():  # quân đồng minh đầu tiên có thể bị giữ
                            possible_pin = (end_row, end_col, direction[0], direction[1])
                        else:  # quân đồng minh thứ hai - không có chiếu hoặc giữ từ hướng này
                            break
                    elif end_piece[0] == enemy_color:
                        enemy_type = end_piece[1]
                        # 5 trường hợp trong điều kiện phức tạp này
                        # 1.) theo chiều ngang ra xa vua và quân cờ là xe
                        # 2.) theo đường chéo ra xa vua và quân cờ là tượng
                        # 3.) 1 ô cách xa vua theo đường chéo và quân cờ là tốt
                        # 4.) bất kỳ hướng nào và quân cờ là hậu
                        # 5.) bất kỳ hướng nào 1 ô cách xa và quân cờ là vua
                        if (0 <= j <= 3 and enemy_type == "R") or (4 <= j <= 7 and enemy_type == "B") or (
                                i == 1 and enemy_type == "p" and (
                                (enemy_color == "w" and 6 <= j <= 7) or (enemy_color == "b" and 4 <= j <= 5))) or (
                                enemy_type == "Q") or (i == 1 and enemy_type == "K"):
                            if possible_pin == ():  # không có quân cờ nào chặn, vì vậy chiếu
                                in_check = True
                                checks.append((end_row, end_col, direction[0], direction[1]))
                                break
                            else:  # quân cờ chặn nên giữ
                                pins.append(possible_pin)
                                break
                        else:  # quân cờ đối thủ không áp dụng chiếu
                            break
                else:
                    break  # ra khỏi bàn cờ
        # kiểm tra chiếu của mã
        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2), (1, -2))
        for move in knight_moves:
            end_row = start_row + move[0]
            end_col = start_col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] == enemy_color and end_piece[1] == "N":  # mã địch tấn công vua
                    in_check = True
                    checks.append((end_row, end_col, move[0], move[1]))
        return in_check, pins, checks

    def getPawnMoves(self, row, col, moves):
        """
        Lấy tất cả các nước đi cho tốt nằm tại hàng, cột và thêm các nước đi vào danh sách.
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.white_to_move:
            move_amount = -1
            start_row = 6
            enemy_color = "b"
            king_row, king_col = self.white_king_location
        else:
            move_amount = 1
            start_row = 1
            enemy_color = "w"
            king_row, king_col = self.black_king_location

        if self.board[row + move_amount][col] == "--":  # tốt di chuyển 1 ô
            if not piece_pinned or pin_direction == (move_amount, 0):
                moves.append(Move((row, col), (row + move_amount, col), self.board))
                if row == start_row and self.board[row + 2 * move_amount][col] == "--":  # tốt di chuyển 2 ô
                    moves.append(Move((row, col), (row + 2 * move_amount, col), self.board))
        if col - 1 >= 0:  # bắt tốt sang trái
            if not piece_pinned or pin_direction == (move_amount, -1):
                if self.board[row + move_amount][col - 1][0] == enemy_color:
                    moves.append(Move((row, col), (row + move_amount, col - 1), self.board))
                if (row + move_amount, col - 1) == self.enpassant_possible:
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_col < col:  # vua nằm bên trái của tốt
                            # trong: giữa vua và tốt;
                            # ngoài: giữa tốt và biên;
                            inside_range = range(king_col + 1, col - 1)
                            outside_range = range(col + 1, 8)
                        else:  # vua nằm bên phải của tốt
                            inside_range = range(king_col - 1, col, -1)
                            outside_range = range(col - 2, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != "--":  # một số quân cờ bên cạnh tốt en-passant chặn
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == enemy_color and (square[1] == "R" or square[1] == "Q"):
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((row, col), (row + move_amount, col - 1), self.board, is_enpassant_move=True))
        if col + 1 <= 7:  # bắt tốt sang phải
            if not piece_pinned or pin_direction == (move_amount, +1):
                if self.board[row + move_amount][col + 1][0] == enemy_color:
                    moves.append(Move((row, col), (row + move_amount, col + 1), self.board))
                if (row + move_amount, col + 1) == self.enpassant_possible:
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_col < col:  # vua nằm bên trái của tốt
                            # trong: giữa vua và tốt;
                            # ngoài: giữa tốt và biên;
                            inside_range = range(king_col + 1, col)
                            outside_range = range(col + 2, 8)
                        else:  # vua nằm bên phải của tốt
                            inside_range = range(king_col - 1, col + 1, -1)
                            outside_range = range(col - 1, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != "--":  # một số quân cờ bên cạnh tốt en-passant chặn
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == enemy_color and (square[1] == "R" or square[1] == "Q"):
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((row, col), (row + move_amount, col + 1), self.board, is_enpassant_move=True))


    def getRookMoves(self, row, col, moves):
        """
        Lấy tất cả các nước đi của xe cho xe nằm tại hàng, cột và thêm các nước đi vào danh sách.
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                if self.board[row][col][1] != "Q":  # không thể loại bỏ hậu từ giữ trên các nước đi của xe, chỉ loại bỏ nó trên các nước đi của tượng
                    self.pins.remove(self.pins[i])
                break

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))  # lên, trái, xuống, phải
        enemy_color = "b" if self.white_to_move else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:  # kiểm tra các nước đi có thể trong giới hạn của bàn cờ
                    if not piece_pinned or pin_direction == direction or pin_direction == (-direction[0], -direction[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":  # ô trống là hợp lệ
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:  # bắt quân địch
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                            break
                        else:  # quân đồng minh
                            break
                else:  # ra khỏi bàn cờ
                    break

    def getKnightMoves(self, row, col, moves):
        """
        Lấy tất cả các nước đi của mã cho mã nằm tại hàng col và thêm các nước đi vào danh sách.
        """
        piece_pinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                self.pins.remove(self.pins[i])
                break

        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2),
                        (1, -2))  # lên/trái lên/phải phải/lên phải/xuống phải xuống/trái
        ally_color = "w" if self.white_to_move else "b"
        for move in knight_moves:
            end_row = row + move[0]
            end_col = col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                if not piece_pinned:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] != ally_color:  # không phải là quân đồng minh - ô trống hoặc quân địch
                        moves.append(Move((row, col), (end_row, end_col), self.board))

    def getBishopMoves(self, row, col, moves):
        """
        Lấy tất cả các nước đi của tượng cho tượng nằm tại hàng, cột và thêm các nước đi vào danh sách.
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = ((-1, -1), (-1, 1), (1, 1), (1, -1))  # đường chéo: lên/trái lên/phải xuống/phải xuống/trái
        enemy_color = "b" if self.white_to_move else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:  # kiểm tra nước đi có nằm trên bàn cờ không
                    if not piece_pinned or pin_direction == direction or pin_direction == (-direction[0], -direction[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":  # ô trống là hợp lệ
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:  # bắt quân địch
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                            break
                        else:  # quân đồng minh
                            break
                else:  # ra khỏi bàn cờ
                    break

    def getQueenMoves(self, row, col, moves):
        """
        Lấy tất cả các nước đi của hậu cho hậu nằm tại hàng, cột và thêm các nước đi vào danh sách.
        """
        self.getBishopMoves(row, col, moves)
        self.getRookMoves(row, col, moves)

    def getKingMoves(self, row, col, moves):
        """
        Lấy tất cả các nước đi của vua cho vua nằm tại hàng, cột và thêm các nước đi vào danh sách.
        """
        row_moves = (-1, -1, -1, 0, 0, 1, 1, 1)
        col_moves = (-1, 0, 1, -1, 1, -1, 0, 1)
        ally_color = "w" if self.white_to_move else "b"
        for i in range(8):
            end_row = row + row_moves[i]
            end_col = col + col_moves[i]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:  # không phải là quân đồng minh - ô trống hoặc quân địch
                    # đặt vua trên ô đích và kiểm tra nước chiếu
                    if ally_color == "w":
                        self.white_king_location = (end_row, end_col)
                    else:
                        self.black_king_location = (end_row, end_col)
                    in_check, pins, checks = self.checkForPinsAndChecks()
                    if not in_check:
                        moves.append(Move((row, col), (end_row, end_col), self.board))
                    # đặt vua trở lại vị trí ban đầu
                    if ally_color == "w":
                        self.white_king_location = (row, col)
                    else:
                        self.black_king_location = (row, col)

    def getCastleMoves(self, row, col, moves):
        """
        Tạo tất cả các nước đi hợp lệ cho vua tại (hàng, cột) và thêm chúng vào danh sách nước đi.
        """
        if self.squareUnderAttack(row, col):
            return  # không thể ăn quân trong tình trạng chiếu
        if (self.white_to_move and self.current_castling_rights.wks) or (
                not self.white_to_move and self.current_castling_rights.bks):
            self.getKingsideCastleMoves(row, col, moves)
        if (self.white_to_move and self.current_castling_rights.wqs) or (
                not self.white_to_move and self.current_castling_rights.bqs):
            self.getQueensideCastleMoves(row, col, moves)

    def getKingsideCastleMoves(self, row, col, moves):
        if self.board[row][col + 1] == '--' and self.board[row][col + 2] == '--':
            if not self.squareUnderAttack(row, col + 1) and not self.squareUnderAttack(row, col + 2):
                moves.append(Move((row, col), (row, col + 2), self.board, is_castle_move=True))

    def getQueensideCastleMoves(self, row, col, moves):
        if self.board[row][col - 1] == '--' and self.board[row][col - 2] == '--' and self.board[row][col - 3] == '--':
            if not self.squareUnderAttack(row, col - 1) and not self.squareUnderAttack(row, col - 2):
                moves.append(Move((row, col), (row, col - 2), self.board, is_castle_move=True))



class CastleRights:
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Move:
    # in chess, fields on the board are described by two symbols, one of them being number between 1-8 (which is corresponding to rows)
    # and the second one being a letter between a-f (corresponding to columns), in order to use this notation we need to map our [row][col] coordinates
    # to match the ones used in the original chess game
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4,
                     "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3,
                     "e": 4, "f": 5, "g": 6, "h": 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, start_square, end_square, board, is_enpassant_move=False, is_castle_move=False):
        self.start_row = start_square[0]
        self.start_col = start_square[1]
        self.end_row = end_square[0]
        self.end_col = end_square[1]
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]
        # pawn promotion
        self.is_pawn_promotion = (self.piece_moved == "wp" and self.end_row == 0) or (
                self.piece_moved == "bp" and self.end_row == 7)
        # en passant
        self.is_enpassant_move = is_enpassant_move
        if self.is_enpassant_move:
            self.piece_captured = "wp" if self.piece_moved == "bp" else "bp"
        # castle move
        self.is_castle_move = is_castle_move

        self.is_capture = self.piece_captured != "--"
        self.moveID = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col

    def __eq__(self, other):
        """
        Overriding the equals method.
        """
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getChessNotation(self):
        if self.is_pawn_promotion:
            return self.getRankFile(self.end_row, self.end_col) + "Q"
        if self.is_castle_move:
            if self.end_col == 1:
                return "0-0-0"
            else:
                return "0-0"
        if self.is_enpassant_move:
            return self.getRankFile(self.start_row, self.start_col)[0] + "x" + self.getRankFile(self.end_row,
                                                                                                self.end_col) + " e.p."
        if self.piece_captured != "--":
            if self.piece_moved[1] == "p":
                return self.getRankFile(self.start_row, self.start_col)[0] + "x" + self.getRankFile(self.end_row,
                                                                                                    self.end_col)
            else:
                return self.piece_moved[1] + "x" + self.getRankFile(self.end_row, self.end_col)
        else:
            if self.piece_moved[1] == "p":
                return self.getRankFile(self.end_row, self.end_col)
            else:
                return self.piece_moved[1] + self.getRankFile(self.end_row, self.end_col)

        # TODO Disambiguating moves

    def getRankFile(self, row, col):
        return self.cols_to_files[col] + self.rows_to_ranks[row]

    def __str__(self):
        if self.is_castle_move:
            return "0-0" if self.end_col == 6 else "0-0-0"

        end_square = self.getRankFile(self.end_row, self.end_col)

        if self.piece_moved[1] == "p":
            if self.is_capture:
                return self.cols_to_files[self.start_col] + "x" + end_square
            else:
                return end_square + "Q" if self.is_pawn_promotion else end_square

        move_string = self.piece_moved[1]
        if self.is_capture:
            move_string += "x"
        return move_string + end_square
