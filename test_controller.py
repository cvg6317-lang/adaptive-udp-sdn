"""Control-plane test; real Mininet integration must also be run in Ubuntu."""
import unittest
from unittest.mock import patch
import controller


class RoutingTest(unittest.TestCase):
    def test_both_paths_install_bidirectional_nonflooding_rules(self):
        ports = {'s1': {'h1':1,'s2':2,'s3':3}, 's2': {'s1':1,'s4':2},
                 's3': {'s1':1,'s4':2}, 's4': {'s2':1,'s3':2,'h2':3}}
        for path in [['s1','s2','s4'],['s1','s3','s4']]:
            with patch.object(controller,'command') as command:
                controller.install(path,ports)
                rules = [c.args for c in command.call_args_list if 'add-flow' in c.args]
                self.assertEqual(len(rules),6)
                for sw in path:
                    self.assertEqual(sum(r[4]==sw for r in rules),2)
                self.assertTrue(all('NORMAL' not in r[-1] and 'FLOOD' not in r[-1] for r in rules))
                forward = next(r[-1] for r in rules if r[4]=='s1' and 'nw_src=10.0.0.1' in r[-1])
                self.assertTrue(forward.endswith('output:'+str(ports['s1'][path[1]])))


if __name__=='__main__': unittest.main()
