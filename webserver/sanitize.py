import re

####################################################################
# input_sanitizer = InputSanitizer()                               #
# user_input = "Hello!@#$%^&*()-_=+[{]}\\|\'\";:/?.>,<123"         #
# sanitized_input = input_sanitizer.sanitize_input(user_input)     #
# print(sanitized_input)                                           #
#    Hello123                                                      #
####################################################################

class InputSanitizer:
   def __init__(self):
        pass

   @staticmethod
   def sanitize_input(input_string):
      sanitized_string = re.sub(r'[^a-zA-Z0-9]', '', input_string)
      return sanitized_string
