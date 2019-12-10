

# def print_f(*args) -> None:
#
#     with open('logs.txt', 'a') as f:
#         f.write(
#             ', '.join(map(str, args)) + '\n'
#         )

print_f = print


class LogContext(object):

    def __enter__(self):
        print_f('-------- start ---------')

    def __exit__(self, exc_type, exc_val, exc_tb):
        print_f('-------- stop ---------')
