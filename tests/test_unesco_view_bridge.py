import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[1]/'tools'/'unesco_mt1_10_view_bridge.py'
spec=importlib.util.spec_from_file_location('bridge',p);b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class TestViewBridge(unittest.TestCase):
 def setUp(self):
  self.view={'profile':b.VIEW_PROFILE,'derived_only':True,'source':{'framework_version':'11.0.0-draft.4','namespace_id':'unit-test','graph_id':'pilot','graph_sha256':'x','registry_sha256':'y','crosswalk_sha256':'z','catalog_sha256':'w'},'requested_locale':'fr','presentation':[{'kind':'entity','semantic_id':'KQ1','lexical':{'status':'direct','term':'education'}},{'kind':'entity','semantic_id':'KQ2','lexical':{'status':'missing'}},{'kind':'property','semantic_id':'KP1','lexical':{'status':'direct','term':'lié à'}}],'assertions':[{'id':'KA1','subject':'KQ1','predicate':'KP1','object':{'kind':'entity','id':'KQ2'},'sources':['KS1']}]} 
  self.selection={'format':'unesco-mt1-10-reviewed-selection/1.0','branch':'unesco-mt1-10','namespace_id':'unit-test','selections':[{'unesco_id':'concept10','local_kq':'KQ1','decision_ref':'review-2026-1'}]}
 def test_safely_preserves_semantic_identity(self):
  x=b.make_handoff(self.view,self.selection,view_sha='123')
  self.assertEqual(x['selected_concepts'],1);self.assertEqual(x['assertions_with_KS'],1)
  self.assertFalse(x['publication_authorized']);self.assertFalse(x['authoritative_authoring_checked'])
  self.assertEqual(x['selections'][0]['assertions'][0]['sources'],['KS1'])
 def test_no_selection_no_guessed_kq(self):
  x=b.make_handoff(self.view,None,view_sha='123')
  self.assertEqual(x['selected_concepts'],0)
 def test_rejects_ka_without_ks(self):
  self.view['assertions'][0]['sources']=[]
  with self.assertRaisesRegex(b.BridgeError,'KS'):b.make_handoff(self.view,self.selection,view_sha='1')
 def test_rejects_kq_inferred_from_missing_view(self):
  self.selection['selections'][0]['local_kq']='KQ999'
  with self.assertRaisesRegex(b.BridgeError,'missing from read view'):b.make_handoff(self.view,self.selection,view_sha='1')
 def test_rejects_unqualified_view(self):
  self.view['source']['framework_version']='11.0.0-draft.3'
  with self.assertRaises(b.BridgeError):b.make_handoff(self.view,self.selection,view_sha='1')
if __name__=='__main__':unittest.main()
