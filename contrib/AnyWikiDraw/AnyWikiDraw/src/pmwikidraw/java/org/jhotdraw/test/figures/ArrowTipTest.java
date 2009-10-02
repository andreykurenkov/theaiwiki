/*
 * @(#)Test.java
 *
 * Project:		JHotdraw - a GUI framework for technical drawings
 *				http://www.jhotdraw.org
 *				http://jhotdraw.sourceforge.net
 * Copyright:	� by the original author(s) and all contributors
 * License:		Lesser GNU Public License (LGPL)
 *				http://www.opensource.org/licenses/lgpl-license.html
 */
package org.jhotdraw.test.figures;

import org.jhotdraw.figures.ArrowTip;
import junit.framework.TestCase;
// JUnitDoclet begin import
// JUnitDoclet end import

/*
 * Generated by JUnitDoclet, a tool provided by
 * ObjectFab GmbH under LGPL.
 * Please see www.junitdoclet.org, www.gnu.org
 * and www.objectfab.de for informations about
 * the tool, the licence and the authors.
 */


// JUnitDoclet begin javadoc_class
/**
 * TestCase ArrowTipTest is generated by
 * JUnitDoclet to hold the tests for ArrowTip.
 * @see org.jhotdraw.figures.ArrowTip
 */
// JUnitDoclet end javadoc_class
public class ArrowTipTest
// JUnitDoclet begin extends_implements
extends TestCase
// JUnitDoclet end extends_implements
{
  // JUnitDoclet begin class
  // instance variables, helper methods, ... put them in this marker
  private ArrowTip arrowtip;
  // JUnitDoclet end class
  
  /**
   * Constructor ArrowTipTest is
   * basically calling the inherited constructor to
   * initiate the TestCase for use by the Framework.
   */
  public ArrowTipTest(String name) {
    // JUnitDoclet begin method ArrowTipTest
    super(name);
    // JUnitDoclet end method ArrowTipTest
  }
  
  /**
   * Factory method for instances of the class to be tested.
   */
  public ArrowTip createInstance() throws Exception {
    // JUnitDoclet begin method testcase.createInstance
    return new ArrowTip();
    // JUnitDoclet end method testcase.createInstance
  }
  
  /**
   * Method setUp is overwriting the framework method to
   * prepare an instance of this TestCase for a single test.
   * It's called from the JUnit framework only.
   */
  protected void setUp() throws Exception {
    // JUnitDoclet begin method testcase.setUp
    super.setUp();
    arrowtip = createInstance();
    // JUnitDoclet end method testcase.setUp
  }
  
  /**
   * Method tearDown is overwriting the framework method to
   * clean up after each single test of this TestCase.
   * It's called from the JUnit framework only.
   */
  protected void tearDown() throws Exception {
    // JUnitDoclet begin method testcase.tearDown
    arrowtip = null;
    super.tearDown();
    // JUnitDoclet end method testcase.tearDown
  }
  
  // JUnitDoclet begin javadoc_method outline()
  /**
   * Method testOutline is testing outline
   * @see org.jhotdraw.figures.ArrowTip#outline(int, int, int, int)
   */
  // JUnitDoclet end javadoc_method outline()
  public void testOutline() throws Exception {
    // JUnitDoclet begin method outline
    // JUnitDoclet end method outline
  }
  
  // JUnitDoclet begin javadoc_method write()
  /**
   * Method testWrite is testing write
   * @see org.jhotdraw.figures.ArrowTip#write(org.jhotdraw.util.StorableOutput)
   */
  // JUnitDoclet end javadoc_method write()
  public void testWrite() throws Exception {
    // JUnitDoclet begin method write
    // JUnitDoclet end method write
  }
  
  // JUnitDoclet begin javadoc_method read()
  /**
   * Method testRead is testing read
   * @see org.jhotdraw.figures.ArrowTip#read(org.jhotdraw.util.StorableInput)
   */
  // JUnitDoclet end javadoc_method read()
  public void testRead() throws Exception {
    // JUnitDoclet begin method read
    // JUnitDoclet end method read
  }
  
  
  
  // JUnitDoclet begin javadoc_method testVault
  /**
   * JUnitDoclet moves marker to this method, if there is not match
   * for them in the regenerated code and if the marker is not empty.
   * This way, no test gets lost when regenerating after renaming.
   * <b>Method testVault is supposed to be empty.</b>
   */
  // JUnitDoclet end javadoc_method testVault
  public void testVault() throws Exception {
    // JUnitDoclet begin method testcase.testVault
    // JUnitDoclet end method testcase.testVault
  }
  

}
