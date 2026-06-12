
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_b8c016f40c11c5f658957b93fc752e34 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_5a1eb0343590d6915ba5b22f68c41852 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.open_sheet", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["width"] : "48px", ["height"] : "48px", ["borderRadius"] : "50%", ["background"] : "#818cf8", ["color"] : "#fff", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center", ["fontSize"] : "26px", ["fontWeight"] : "300", ["cursor"] : "pointer", ["margin"] : "0 10px", ["flexShrink"] : "0", ["boxShadow"] : "0 4px 16px #818cf880", ["&:active"] : ({ ["transform"] : "scale(0.93)" }) }),onClick:on_click_5a1eb0343590d6915ba5b22f68c41852},children)
    )
});
