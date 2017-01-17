from re import (
    escape as re_escape,
    sub as re_sub,
    search as re_search,
)
from time import sleep

from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.netmiko_globals import BACKSPACE_CHAR


class EdgeCoreSSH(CiscoSSHConnection):
    def establish_connection(self, width=None, height=None):
        return super(EdgeCoreSSH, self).establish_connection(
            width=24,
            height=24,
        )

    def check_config_mode(self, check_string=')#', pattern=''):
        """Checks if the device is in configuration mode or not."""
        return super(
            EdgeCoreSSH,
            self
        ).check_config_mode(
            check_string=check_string
        )

    def config_mode(self, config_command='configure', pattern=''):
        """Enter configuration mode."""
        return super(
            EdgeCoreSSH,
            self
        ).config_mode(
            config_command=config_command
        )

    def exit_config_mode(self, exit_config='exit', pattern=''):
        """Exit configuration mode."""
        return super(
            EdgeCoreSSH,
            self
        ).exit_config_mode(
            exit_config=exit_config
        )

    def exit_enable_mode(self, exit_command='exit'):
        """Exit enable mode."""
        return super(
            EdgeCoreSSH,
            self
        ).exit_enable_mode(
            exit_command=exit_command
        )

    @staticmethod
    def strip_backspaces(output):
        """Strip any backspace characters out of the output."""
        output = re_sub(
            '[\b]{10}.*[\b]{10}',
            '',
            output,
        )
        return output

    @staticmethod
    def strip_page_string(page_string, string_buffer):
        output = string_buffer
        output = re_sub(
            page_string,
            '',
            output
        )
        return output

    def send_command(self, command_string, expect_string=None,
                     delay_factor=1, max_loops=500, auto_find_prompt=True,
                     strip_prompt=True, strip_command=True,
                     page_string='---More---'):
        '''
        Send command to network device retrieve output until router_prompt or
         expect_string

        By default this method will keep waiting to receive data until the
        network device prompt is detected.
        The current network device prompt will be determined automatically.

        command_string = command to execute
        expect_string = pattern to search for uses re.search (use raw strings)
        delay_factor = decrease the initial delay before we start looking for data
        max_loops = number of iterations before we give up and raise an exception
        strip_prompt = strip the trailing prompt from the output
        strip_command = strip the leading command from the output
        page_string = pagination string
        '''

        debug = False
        delay_factor = self.select_delay_factor(delay_factor)

        # Find the current router prompt
        if expect_string is None:
            if auto_find_prompt:
                try:
                    prompt = self.find_prompt(delay_factor=delay_factor)
                except ValueError:
                    prompt = self.base_prompt
                if debug:
                    print("Found prompt: {}".format(prompt))
            else:
                prompt = self.base_prompt
            search_pattern = re_escape(prompt.strip())
        else:
            search_pattern = expect_string

        command_string = self.normalize_cmd(command_string)
        if debug:
            print("Command is: {0}".format(command_string))
            print(
                "Search to stop "
                "receiving data is: '{0}'".format(
                    search_pattern
                )
            )

        sleep(delay_factor * .2)
        self.clear_buffer()
        self.write_channel(command_string)

        # Initial delay after sending command
        i = 1
        # Keep reading data until search_pattern is found (or max_loops)
        output = ''
        while i <= max_loops:
            new_data = self.read_channel()
            if new_data:

                if page_string is not None and re_search(
                        page_string,
                        new_data,
                ):
                    self.write_channel('  ')
                    new_data = self.strip_page_string(
                        page_string,
                        new_data
                    )
                    i = 0

                output += new_data
                if debug:
                    print("{}:{}".format(i, output))

                try:
                    lines = output.split("\n")
                    first_line = lines[0]
                    # First line is the echo line containing the command.
                    # In certain situations it gets repainted and needs filtered
                    if BACKSPACE_CHAR in first_line:
                        pattern = search_pattern + r'.*$'
                        first_line = re_sub(
                            pattern,
                            repl='',
                            string=first_line
                        )
                        lines[0] = first_line
                        output = "\n".join(lines)
                except IndexError:
                    pass
                if re_search(
                        search_pattern,
                        output,
                ):
                    break
            else:
                sleep(delay_factor * .2)
            i += 1
        else:
            raise IOError(
                "Search pattern never detected in "
                "send_command_expect: {0}".format(
                    search_pattern
                )
            )

        output = self._sanitize_output(
            output,
            strip_command=strip_command,
            command_string=command_string,
            strip_prompt=strip_prompt,
        )
        return output

    def _sanitize_output(self, output, strip_command=False,
                         command_string=None, strip_prompt=False):
        output = self.strip_backspaces(output)
        return super(
            EdgeCoreSSH,
            self
        )._sanitize_output(
            output,
            strip_command=strip_command,
            command_string=command_string,
            strip_prompt=strip_prompt,
        )
