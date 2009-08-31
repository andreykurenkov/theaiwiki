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
package org.jhotdraw.test.standard;

import org.jhotdraw.standard.ChopBoxConnector;
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
 * TestCase ChopBoxConnectorTest is generated by
 * JUnitDoclet to hold the tests for ChopBoxConnector.
 * @see org.jhotdraw.standard.ChopBoxConnector
 */
// JUnitDoclet end javadoc_class
public class ChopBoxConnectorTest
// JUnitDoclet begin extends_implements
extends TestCase
// JUnitDoclet end extends_implements
{
	// JUnitDoclet begin class
	// instance variables, helper methods, ... put them in this marker
	private ChopBoxConnector chopboxconnector;
	// JUnitDoclet end class

	/**
	 * Constructor ChopBoxConnectorTest is
	 * basically calling the inherited constructor to
	 * initiate the TestCase for use by the Framework.
	 */
	public ChopBoxConnectorTest(String name) {
		// JUnitDoclet begin method ChopBoxConnectorTest
		super(name);
		// JUnitDoclet end method ChopBoxConnectorTest
	}

	/**
	 * Factory method for instances of the class to be tested.
	 */
	public ChopBoxConnector createInstance() throws Exception {
		// JUnitDoclet begin method testcase.createInstance
		return new ChopBoxConnector();
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
		chopboxconnector = createInstance();
		// JUnitDoclet end method testcase.setUp
	}

	/**
	 * Method tearDown is overwriting the framework method to
	 * clean up after each single test of this TestCase.
	 * It's called from the JUnit framework only.
	 */
	protected void tearDown() throws Exception {
		// JUnitDoclet begin method testcase.tearDown
		chopboxconnector = null;
		super.tearDown();
		// JUnitDoclet end method testcase.tearDown
	}

	// JUnitDoclet begin javadoc_method findStart()
	/**
	 * Method testFindStart is testing findStart
	 * @see org.jhotdraw.standard.ChopBoxConnector#findStart(org.jhotdraw.framework.ConnectionFigure)
	 */
	// JUnitDoclet end javadoc_method findStart()
	public void testFindStart() throws Exception {
		// JUnitDoclet begin method findStart
		// JUnitDoclet end method findStart
	}

	// JUnitDoclet begin javadoc_method findEnd()
	/**
	 * Method testFindEnd is testing findEnd
	 * @see org.jhotdraw.standard.ChopBoxConnector#findEnd(org.jhotdraw.framework.ConnectionFigure)
	 */
	// JUnitDoclet end javadoc_method findEnd()
	public void testFindEnd() throws Exception {
		// JUnitDoclet begin method findEnd
		// JUnitDoclet end method findEnd
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
